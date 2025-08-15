"""
Stripe Billing endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import stripe
from datetime import datetime
import logging

from src.core.config import settings
from src.core.database import get_db
from src.models.asset_models import User

logger = logging.getLogger(__name__)
router = APIRouter()

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-checkout-session")
async def create_checkout_session(payload: dict, db: Session = Depends(get_db)):
    """
    Create a subscription Checkout Session for a user.
    payload: { username: string, success_url?: string, cancel_url?: string }
    """
    try:
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="username is required")
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        success_url = payload.get("success_url") or f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = payload.get("cancel_url") or f"{settings.FRONTEND_URL}/billing/canceled"

        customer_id = user.stripe_customer_id
        if not customer_id:
            customer = stripe.Customer.create(email=user.email, name=user.username)
            customer_id = customer["id"]
            user.stripe_customer_id = customer_id
            db.commit()

        session = stripe.checkout.Session.create(
            success_url=success_url,
            cancel_url=cancel_url,
            mode="subscription",
            payment_method_types=["card"],
            customer=customer_id,
            line_items=[
                {
                    "price": settings.STRIPE_PRICE_ID,
                    "quantity": 1,
                }
            ],
        )

        return {"id": session["id"], "url": session.get("url")}

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout session error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create checkout session")


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhook events to set access on subscription activation."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    try:
        if settings.STRIPE_WEBHOOK_SECRET:
            event = stripe.Webhook.construct_event(
                payload=payload, sig_header=sig_header, secret=settings.STRIPE_WEBHOOK_SECRET
            )
        else:
            event = stripe.Event.construct_from(request.json(), stripe.api_key)
    except Exception as e:
        logger.error(f"Webhook signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid payload")

    try:
        if event["type"] in ("customer.subscription.created", "customer.subscription.updated"):
            subscription = event["data"]["object"]
            customer_id = subscription.get("customer")
            status_value = subscription.get("status")
            current_period_end = subscription.get("current_period_end")
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                user.stripe_subscription_status = status_value
                user.stripe_current_period_end = datetime.utcfromtimestamp(current_period_end) if current_period_end else None
                user.has_access = status_value in ("active", "trialing")
                db.commit()

        if event["type"] in ("customer.subscription.deleted", "invoice.payment_failed"):
            data_object = event["data"]["object"]
            customer_id = data_object.get("customer")
            user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
            if user:
                user.stripe_subscription_status = "canceled"
                user.has_access = False
                db.commit()

        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook handling error: {e}")
        raise HTTPException(status_code=500, detail="Webhook handling failed")


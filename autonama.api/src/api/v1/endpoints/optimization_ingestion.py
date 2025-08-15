#!/usr/bin/env python3
"""
Optimization Data Ingestion API Endpoints

This module provides API endpoints for:
1. Triggering optimization data ingestion
2. Retrieving alerts
3. Retrieving asset analytics
4. Retrieving optimization summary
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

router = APIRouter()

def get_data_path():
    """Get the path to the ingested data"""
    return Path("/app/public/data/api")

@router.get("/alerts")
async def get_alerts():
    """Get alerts from ingested JSON files"""
    try:
        data_path = get_data_path()
        alerts_file = data_path / "alerts.json"
        
        if not alerts_file.exists():
            raise HTTPException(status_code=404, detail="Alerts data not found. Please run the ingestion script first.")
        
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
        
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@router.get("/analytics")
async def get_analytics():
    """Get analytics from ingested JSON files"""
    try:
        data_path = get_data_path()
        analytics_file = data_path / "analytics.json"
        
        if not analytics_file.exists():
            raise HTTPException(status_code=404, detail="Analytics data not found. Please run the ingestion script first.")
        
        with open(analytics_file, 'r') as f:
            analytics = json.load(f)
        
        return analytics
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@router.get("/analytics/{symbol}")
async def get_asset_analytics(symbol: str):
    """Get analytics for a specific asset"""
    try:
        data_path = get_data_path()
        asset_file = data_path / "assets" / f"{symbol}.json"
        
        if not asset_file.exists():
            raise HTTPException(status_code=404, detail=f"Analytics for {symbol} not found.")
        
        with open(asset_file, 'r') as f:
            analytics = json.load(f)
        
        return analytics
    except Exception as e:
        logger.error(f"Error fetching asset analytics for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch asset analytics: {str(e)}")

@router.get("/summary")
async def get_summary():
    """Get summary from ingested JSON files"""
    try:
        data_path = get_data_path()
        summary_file = data_path / "summary.json"
        
        if not summary_file.exists():
            raise HTTPException(status_code=404, detail="Summary data not found. Please run the ingestion script first.")
        
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        return summary
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch summary: {str(e)}")

@router.get("/assets")
async def get_assets():
    """Get assets from ingested JSON files"""
    try:
        data_path = get_data_path()
        assets_file = data_path / "assets.json"
        
        if not assets_file.exists():
            raise HTTPException(status_code=404, detail="Assets data not found. Please run the ingestion script first.")
        
        with open(assets_file, 'r') as f:
            assets = json.load(f)
        
        return assets
    except Exception as e:
        logger.error(f"Error fetching assets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch assets: {str(e)}") 
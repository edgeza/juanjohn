#!/usr/bin/env python3
"""
Generate alerts for all assets in the database
"""

import psycopg2
from datetime import datetime
import random

def get_timescale_connection():
    """Get TimescaleDB connection"""
    return psycopg2.connect(
        host="postgres",
        database="autonama",
        user="postgres",
        password="postgres"
    )

def get_all_assets():
    """Get all assets from current_prices table"""
    conn = get_timescale_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT DISTINCT symbol, price, volume_24h
    FROM trading.current_prices
    ORDER BY volume_24h DESC
    """
    
    cursor.execute(query)
    assets = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return assets

def generate_mock_alert(symbol, price, volume_24h):
    """Generate a mock alert for an asset"""
    # Determine signal based on volume and price
    if volume_24h > 100000000:  # High volume
        signal = random.choice(['BUY', 'SELL'])
    else:
        signal = random.choice(['BUY', 'SELL', 'HOLD'])
    
    # Generate realistic potential return
    if signal == 'BUY':
        potential_return = random.uniform(5.0, 150.0)
    elif signal == 'SELL':
        potential_return = random.uniform(5.0, 100.0)
    else:  # HOLD
        potential_return = random.uniform(0.5, 10.0)
    
    # Generate other metrics
    signal_strength = random.uniform(0.0, 1.0)
    risk_level = random.choice(['LOW', 'MEDIUM', 'HIGH'])
    
    return {
        'symbol': symbol,
        'signal': signal,
        'current_price': float(price),
        'potential_return': round(potential_return, 2),
        'signal_strength': round(signal_strength, 2),
        'risk_level': risk_level,
        'interval': '1d',
        'timestamp': datetime.now().isoformat()
    }

def insert_alert(alert_data):
    """Insert alert into database"""
    conn = get_timescale_connection()
    cursor = conn.cursor()
    
    query = """
    INSERT INTO trading.alerts (
        symbol, signal, current_price, potential_return, 
        signal_strength, risk_level, interval, timestamp, created_at
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, NOW()
    )
    """
    
    cursor.execute(query, (
        alert_data['symbol'],
        alert_data['signal'],
        alert_data['current_price'],
        alert_data['potential_return'],
        alert_data['signal_strength'],
        alert_data['risk_level'],
        alert_data['interval'],
        alert_data['timestamp']
    ))
    
    conn.commit()
    cursor.close()
    conn.close()

def main():
    """Generate alerts for all assets"""
    print("Fetching all assets from database...")
    assets = get_all_assets()
    print(f"Found {len(assets)} assets")
    
    print("Generating alerts...")
    for i, (symbol, price, volume_24h) in enumerate(assets, 1):
        alert = generate_mock_alert(symbol, price, volume_24h)
        insert_alert(alert)
        print(f"[{i}/{len(assets)}] Generated alert for {symbol}: {alert['signal']} - {alert['potential_return']}%")
    
    print(f"Successfully generated alerts for {len(assets)} assets!")

if __name__ == "__main__":
    main() 
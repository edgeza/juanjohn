#!/usr/bin/env python3
"""
Crypto Engine Dashboard - Streamlit Visualization

This dashboard provides a comprehensive interface for testing and visualizing
the crypto engine analysis results, ensuring complete export functionality.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import json
import os
import sqlite3
from datetime import datetime, timedelta
import time
from crypto_engine import CryptoEngine

# Page configuration
st.set_page_config(
    page_title="Crypto Engine Dashboard",
    page_icon="₿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .signal-buy { border-left-color: #27ae60 !important; }
    .signal-sell { border-left-color: #e74c3c !important; }
    .signal-hold { border-left-color: #f39c12 !important; }
    .status-success { color: #27ae60; font-weight: bold; }
    .status-error { color: #e74c3c; font-weight: bold; }
    .status-warning { color: #f39c12; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def load_engine():
    """Load crypto engine without caching to avoid serialization issues"""
    try:
        engine = CryptoEngine("config.json")
        return engine, None
    except Exception as e:
        return None, str(e)

def get_database_info(engine):
    """Get database information without caching"""
    try:
        conn = sqlite3.connect(engine.db_path)
        
        # Get table info
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get record counts
        counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        
        # Get latest analysis
        if 'crypto_analysis_results' in tables:
            cursor.execute("""
                SELECT symbol, signal, current_price, potential_return, created_at
                FROM crypto_analysis_results
                ORDER BY created_at DESC
                LIMIT 10
            """)
            latest_results = cursor.fetchall()
        else:
            latest_results = []
        
        conn.close()
        return tables, counts, latest_results
    except Exception as e:
        return [], {}, []

def create_price_chart(engine, symbol, days=365):
    """Create price chart with regression bands"""
    try:
        # Get historical data from database
        conn = sqlite3.connect(engine.db_path)
        query = """
            SELECT timestamp, open, high, low, close, volume
            FROM crypto_historical_data
            WHERE symbol = ? AND interval = '1d'
            ORDER BY timestamp DESC
            LIMIT ?
        """
        df = pd.read_sql_query(query, conn, params=(symbol, days))
        conn.close()
        
        if df.empty:
            return None
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df = df.sort_index()
        
        # Calculate regression bands
        close_data = df['close']
        processed_data = engine.preprocess_data(close_data)
        
        pf, indicators, entries, exits = engine.calculate_polynomial_regression(processed_data)
        
        if indicators is None:
            return None
        
        # Create plot
        fig = go.Figure()
        
        # Price line
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['close'],
            mode='lines',
            name='Price',
            line=dict(color='#2c3e50', width=2)
        ))
        
        # Regression line
        fig.add_trace(go.Scatter(
            x=indicators.index,
            y=indicators['regression_line'],
            mode='lines',
            name='Regression',
            line=dict(color='#3498db', width=2, dash='dash')
        ))
        
        # Upper band
        fig.add_trace(go.Scatter(
            x=indicators.index,
            y=indicators['upper_band'],
            mode='lines',
            name='Upper Band',
            line=dict(color='#e74c3c', width=1),
            fill='tonexty',
            fillcolor='rgba(231, 76, 60, 0.1)'
        ))
        
        # Lower band
        fig.add_trace(go.Scatter(
            x=indicators.index,
            y=indicators['lower_band'],
            mode='lines',
            name='Lower Band',
            line=dict(color='#27ae60', width=1),
            fill='tonexty',
            fillcolor='rgba(39, 174, 96, 0.1)'
        ))
        
        # Current price marker
        current_price = df['close'].iloc[-1]
        fig.add_trace(go.Scatter(
            x=[df.index[-1]],
            y=[current_price],
            mode='markers',
            name='Current Price',
            marker=dict(color='#f39c12', size=10, symbol='diamond')
        ))
        
        fig.update_layout(
            title=f'{symbol} Price Analysis',
            xaxis_title='Date',
            yaxis_title='Price (USDT)',
            height=500,
            showlegend=True
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating chart for {symbol}: {e}")
        return None

def create_signal_distribution(results_df):
    """Create signal distribution chart"""
    if results_df.empty:
        return None
    
    signal_counts = results_df['signal'].value_counts()
    
    fig = px.pie(
        values=signal_counts.values,
        names=signal_counts.index,
        title='Signal Distribution',
        color_discrete_map={
            'BUY': '#27ae60',
            'SELL': '#e74c3c',
            'HOLD': '#f39c12'
        }
    )
    
    fig.update_layout(height=400)
    return fig

def create_return_analysis(results_df):
    """Create return analysis chart"""
    if results_df.empty:
        return None
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Potential Return Distribution', 'Price vs Potential Return'),
        vertical_spacing=0.1
    )
    
    # Potential return distribution
    fig.add_trace(
        go.Histogram(
            x=results_df['potential_return'],
            nbinsx=20,
            name='Potential Return',
            marker_color='#3498db'
        ),
        row=1, col=1
    )
    
    # Scatter plot - use current_price instead of total_return
    fig.add_trace(
        go.Scatter(
            x=results_df['current_price'],
            y=results_df['potential_return'],
            mode='markers',
            text=results_df['symbol'],
            name='Price vs Return',
            marker=dict(
                color=results_df['signal'].map({'BUY': '#27ae60', 'SELL': '#e74c3c', 'HOLD': '#f39c12'}),
                size=8
            )
        ),
        row=2, col=1
    )
    
    fig.update_layout(height=600, showlegend=False)
    return fig

def export_results(engine, results_df):
    """Export results in various formats"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Convert DataFrame to list of dicts for engine export
    results_list = results_df.to_dict('records')
    
    # Export using engine methods
    csv_file = engine.save_results_to_csv(results_list, f"dashboard_export_{timestamp}.csv")
    json_file = engine.save_results_to_json(results_list, f"dashboard_export_{timestamp}.json")
    
    return csv_file, json_file

def main():
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>₿ Crypto Engine Dashboard</h1>
            <p>Data Visualization Interface for Optimization Results</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Auto-load latest export folder on startup
    if 'analysis_results' not in st.session_state:
        base_export_dir = "export_results"
        if os.path.exists(base_export_dir):
            # Get all optimization run folders
            subfolders = [f for f in os.listdir(base_export_dir) 
                         if os.path.isdir(os.path.join(base_export_dir, f)) and 
                         f.startswith('optimization_run_')]
            
            if subfolders:
                # Sort by folder name (date-time) and get the latest
                latest_folder = max(subfolders)
                export_dir = os.path.join(base_export_dir, latest_folder)
                
                st.success(f"📁 Loading from latest folder: {latest_folder}")
                
                # Load all files from the subdirectories within the latest folder
                all_results = []
                all_summaries = []
                loaded_files = []
                seen_symbols = set()  # To track unique symbols and avoid duplicates
                
                # Define subdirectories to check
                subdirs = ['alerts', 'analytics', 'summary', 'plots']
                
                for subdir in subdirs:
                    subdir_path = os.path.join(export_dir, subdir)
                    if os.path.exists(subdir_path):
                        json_files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                        for json_file in json_files:
                            try:
                                file_path = os.path.join(subdir_path, json_file)
                                with open(file_path, 'r') as f:
                                    export_data = json.load(f)
                                
                                loaded_files.append(f"{subdir}/{json_file}")
                                
                                # Handle different data structures based on file type
                                if subdir == 'alerts':
                                    # Alerts now contain ALL assets with consistent structure
                                    if isinstance(export_data, list):
                                        # Add all alerts (they now contain complete dataset)
                                        for alert in export_data:
                                            symbol = alert.get('symbol', '')
                                            if symbol and symbol not in seen_symbols:
                                                all_results.append(alert)
                                                seen_symbols.add(symbol)
                                    else:
                                        all_results.append(export_data)
                                        
                                elif subdir == 'analytics':
                                    # Analytics file contains individual_analyses - this is the complete dataset
                                    if 'individual_analyses' in export_data:
                                        # Clear previous results and use analytics as the primary source
                                        all_results = []  # Reset to use analytics as primary
                                        seen_symbols = set()  # Reset seen symbols
                                        
                                        # Add all analytics data
                                        for analysis in export_data['individual_analyses']:
                                            symbol = analysis.get('symbol', '')
                                            if symbol:
                                                all_results.append(analysis)
                                                seen_symbols.add(symbol)
                                    if 'summary' in export_data:
                                        all_summaries.append(export_data['summary'])
                                        
                                elif subdir == 'summary':
                                    # Summary file contains analysis_summary
                                    if 'analysis_summary' in export_data:
                                        all_summaries.append(export_data['analysis_summary'])
                                        
                                elif subdir == 'plots':
                                    # Plots file contains potential_returns - only add if not already in analytics
                                    if 'potential_returns' in export_data:
                                        # Only add plots that aren't duplicates
                                        for plot in export_data['potential_returns']:
                                            symbol = plot.get('symbol', '')
                                            if symbol and symbol not in seen_symbols:
                                                all_results.append(plot)
                                                seen_symbols.add(symbol)
                                        # Create summary for this file
                                        all_summaries.append({
                                            'total_assets': len(export_data['potential_returns']),
                                            'buy_signals': len([r for r in export_data['potential_returns'] if r.get('signal') == 'BUY']),
                                            'sell_signals': len([r for r in export_data['potential_returns'] if r.get('signal') == 'SELL']),
                                            'hold_signals': len([r for r in export_data['potential_returns'] if r.get('signal') == 'HOLD']),
                                            'avg_potential_return': sum([r.get('potential_return', 0) for r in export_data['potential_returns']]) / len(export_data['potential_returns']),
                                            'avg_total_return': 0
                                        })
                                        
                            except Exception as e:
                                st.warning(f"Could not load export file {subdir}/{json_file}: {e}")
                
                # Also check for manifest file in the main directory
                manifest_path = os.path.join(export_dir, 'manifest_*.json')
                import glob
                manifest_files = glob.glob(manifest_path)
                if manifest_files:
                    loaded_files.append(f"manifest/{os.path.basename(manifest_files[0])}")
                
                # Store results (no need to deduplicate since they're from the same folder)
                if all_results:
                    st.session_state['analysis_results'] = all_results
                    
                    # Create combined summary
                    if all_summaries:
                        combined_summary = {
                            'total_assets': sum(s.get('total_assets', 0) for s in all_summaries),
                            'buy_signals': sum(s.get('buy_signals', 0) for s in all_summaries),
                            'sell_signals': sum(s.get('sell_signals', 0) for s in all_summaries),
                            'hold_signals': sum(s.get('hold_signals', 0) for s in all_summaries),
                            'avg_potential_return': sum(s.get('avg_potential_return', 0) for s in all_summaries) / len(all_summaries) if all_summaries else 0,
                            'avg_total_return': 0
                        }
                    else:
                        # Create summary from results
                        combined_summary = {
                            'total_assets': len(all_results),
                            'buy_signals': len([r for r in all_results if r.get('signal') == 'BUY']),
                            'sell_signals': len([r for r in all_results if r.get('signal') == 'SELL']),
                            'hold_signals': len([r for r in all_results if r.get('signal') == 'HOLD']),
                            'avg_potential_return': sum([r.get('potential_return', 0) for r in all_results]) / len(all_results) if all_results else 0,
                            'avg_total_return': 0
                        }
                    
                    st.session_state['analysis_summary'] = combined_summary
                    st.success(f"✅ Loaded {len(loaded_files)} files from {latest_folder} with {len(all_results)} results")
                    st.info(f"📁 Files loaded: {', '.join(loaded_files)}")
                else:
                    st.warning("No results found in export files")
            else:
                st.warning(f"No export files found in {latest_folder}")
        else:
            st.warning("No optimization run folders found in export_results")
    else:
        st.warning("Export directory not found")
    
    # Sidebar
    st.sidebar.title("🔧 Controls")
    
    # Load engine
    engine, error = load_engine()
    if error:
        st.error(f"Failed to load engine: {error}")
        st.stop()
    
    # Database info
    tables, counts, latest_results = get_database_info(engine)
    
    st.sidebar.markdown("### 📊 Database Status")
    for table, count in counts.items():
        st.sidebar.markdown(f"**{table}**: {count} records")
    
    # Auto-load export folders
    st.sidebar.markdown("### 📁 Optimization Runs")
    export_dir = "export_results"
    if os.path.exists(export_dir):
        # Get all optimization run folders
        subfolders = [f for f in os.listdir(export_dir) 
                     if os.path.isdir(os.path.join(export_dir, f)) and 
                     f.startswith('optimization_run_')]
        
        if subfolders:
            # Sort by folder name (date-time) and get the latest
            latest_folder = max(subfolders)
            st.sidebar.success(f"Found {len(subfolders)} optimization runs")
            st.sidebar.info(f"Latest: {latest_folder}")
            
            # Show folder contents
            latest_path = os.path.join(export_dir, latest_folder)
            subdirs = ['alerts', 'analytics', 'summary', 'plots', 'raw_data']
            file_counts = {}
            
            for subdir in subdirs:
                subdir_path = os.path.join(latest_path, subdir)
                if os.path.exists(subdir_path):
                    json_files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                    file_counts[subdir] = len(json_files)
            
            st.sidebar.markdown("**Folder Contents:**")
            for subdir, count in file_counts.items():
                st.sidebar.markdown(f"  • {subdir}: {count} files")
            
            if st.sidebar.button("🔄 Reload Latest Run", type="secondary"):
                st.rerun()
        else:
            st.sidebar.warning("No optimization runs found")
    else:
        st.sidebar.warning("Export directory not found")
    
    # Data visualization controls
    st.sidebar.markdown("### 📊 Data Visualization")
    
    # Show loaded data info
    if 'analysis_results' in st.session_state:
        results = st.session_state['analysis_results']
        st.sidebar.success(f"✅ Loaded {len(results)} results")
        
        # Show data source info
        base_export_dir = "export_results"
        if os.path.exists(base_export_dir):
            subfolders = [f for f in os.listdir(base_export_dir) 
                         if os.path.isdir(os.path.join(base_export_dir, f)) and 
                         f.startswith('optimization_run_')]
            if subfolders:
                latest_folder = max(subfolders)
                export_dir = os.path.join(base_export_dir, latest_folder)
                export_files = [f for f in os.listdir(export_dir) if f.endswith('.json')]
                st.sidebar.info(f"📁 From {latest_folder} ({len(export_files)} files)")
            else:
                st.sidebar.warning("No date-time folders found")
        else:
            st.sidebar.warning("Export directory not found")
    else:
        st.sidebar.warning("No data loaded")
    
    # Main content
    if 'analysis_results' in st.session_state:
        results = st.session_state['analysis_results']
        summary = st.session_state['analysis_summary']
        
        # Show what data Docker would see
        st.markdown("### 🔍 Data Available to Docker")
        st.info("This is the data that would be available to the Docker containers:")
        
        # Show latest optimization run info
        export_dir = "export_results"
        if os.path.exists(export_dir):
            # Get all optimization run folders
            subfolders = [f for f in os.listdir(export_dir) 
                         if os.path.isdir(os.path.join(export_dir, f)) and 
                         f.startswith('optimization_run_')]
            
            if subfolders:
                # Sort by folder name (date-time) and get the latest
                latest_folder = max(subfolders)
                latest_path = os.path.join(export_dir, latest_folder)
                
                st.success(f"✅ Found latest optimization run: {latest_folder}")
                
                # Show folder contents
                subdirs = ['alerts', 'analytics', 'summary', 'plots', 'raw_data']
                total_files = 0
                
                for subdir in subdirs:
                    subdir_path = os.path.join(latest_path, subdir)
                    if os.path.exists(subdir_path):
                        json_files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                        total_files += len(json_files)
                        for json_file in json_files:
                            file_path = os.path.join(subdir_path, json_file)
                            file_size = os.path.getsize(file_path)
                            file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                            st.text(f"📄 {subdir}/{json_file} ({file_size:,} bytes, {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                
                # Also check for manifest and README
                manifest_files = [f for f in os.listdir(latest_path) if f.startswith('manifest_') and f.endswith('.json')]
                for manifest_file in manifest_files:
                    file_path = os.path.join(latest_path, manifest_file)
                    file_size = os.path.getsize(file_path)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    st.text(f"📄 {manifest_file} ({file_size:,} bytes, {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                
                st.info(f"📁 Total files in optimization run: {total_files + len(manifest_files)}")
            else:
                st.warning("⚠️ No optimization runs found - Docker would not have data to display")
        else:
            st.error("❌ Export directory not found - Docker would not have data to display")
        
        st.markdown("---")
        
        # Docker Preview Section
        st.markdown("### 🐳 Docker Preview")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📡 API Endpoints")
            st.info("""
            **API Container would serve:**
            - `/api/v1/assets` - Asset list
            - `/api/v1/signals` - Trading signals
            - `/api/v1/analytics` - Performance analytics
            - `/api/v1/optimization/results` - Optimization results
            """)
        
        with col2:
            st.markdown("#### 🌐 Web App Pages")
            st.info("""
            **Web Container would display:**
            - `/assets` - Asset dashboard
            - `/signals` - Signal cards
            - `/analytics` - Performance charts
            - `/optimization` - Results analysis
            """)
        
        # Show what data each container would receive
        st.markdown("#### 📊 Data Available to Containers")
        
        # Check what files are available for each container
        export_dir = "export_results"
        if os.path.exists(export_dir):
            export_files = [f for f in os.listdir(export_dir) if f.endswith('.json')]
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**API Container Data:**")
                api_files = [f for f in export_files if any(x in f for x in ['alerts', 'analytics', 'summary'])]
                for file in api_files:
                    file_size = os.path.getsize(os.path.join(export_dir, file))
                    st.text(f"✅ {file} ({file_size:,} bytes)")
            
            with col2:
                st.markdown("**Web Container Data:**")
                web_files = [f for f in export_files if any(x in f for x in ['plots', 'charts', 'manifest'])]
                for file in web_files:
                    file_size = os.path.getsize(os.path.join(export_dir, file))
                    st.text(f"✅ {file} ({file_size:,} bytes)")
        
        st.markdown("---")
        
        # All Data Sources Section
        st.markdown("### 📋 All Data Sources")
        
        # Show all export files and their contents
        base_export_dir = "export_results"
        if os.path.exists(base_export_dir):
            # Get all optimization run folders
            subfolders = [f for f in os.listdir(base_export_dir) 
                         if os.path.isdir(os.path.join(base_export_dir, f)) and 
                         f.startswith('optimization_run_')]
            
            if subfolders:
                # Sort folders by date-time and get the latest
                subfolders.sort(reverse=True)
                latest_folder = subfolders[0]
                export_dir = os.path.join(base_export_dir, latest_folder)
                
                # Count files in each subdirectory
                subdirs = ['alerts', 'analytics', 'summary', 'plots', 'raw_data']
                file_counts = {}
                all_files = []
                
                for subdir in subdirs:
                    subdir_path = os.path.join(export_dir, subdir)
                    if os.path.exists(subdir_path):
                        json_files = [f for f in os.listdir(subdir_path) if f.endswith('.json')]
                        file_counts[subdir] = len(json_files)
                        for json_file in json_files:
                            all_files.append(f"{subdir}/{json_file}")
                
                # Also check for manifest files in main directory
                manifest_files = [f for f in os.listdir(export_dir) if f.startswith('manifest_') and f.endswith('.json')]
                file_counts['manifest'] = len(manifest_files)
                all_files.extend(manifest_files)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 File Types Summary")
                    for subdir, count in file_counts.items():
                        st.metric(f"{subdir.title()} Files", count)
                
                with col2:
                    st.markdown(f"#### 📄 Files in {latest_folder}")
                    for file in sorted(all_files):
                        if '/' in file:  # Subdirectory file
                            file_path = os.path.join(export_dir, file)
                        else:  # Main directory file
                            file_path = os.path.join(export_dir, file)
                        file_size = os.path.getsize(file_path)
                        file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                        st.text(f"📄 {file} ({file_size:,} bytes, {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                
                # Show sample data from each file type
                st.markdown("#### 🔍 Data Samples")
                
                sample_tabs = st.tabs(["Alerts", "Analytics", "Plots", "Summary", "Manifest"])
                
                with sample_tabs[0]:
                    alerts_path = os.path.join(export_dir, "alerts")
                    if os.path.exists(alerts_path):
                        alerts_files = [f for f in os.listdir(alerts_path) if f.endswith('.json')]
                        if alerts_files:
                            latest_alerts = max(alerts_files, key=lambda x: os.path.getctime(os.path.join(alerts_path, x)))
                            try:
                                with open(os.path.join(alerts_path, latest_alerts), 'r') as f:
                                    alerts_data = json.load(f)
                                st.json(alerts_data[:3] if isinstance(alerts_data, list) else alerts_data)
                            except Exception as e:
                                st.error(f"Error reading alerts: {e}")
                        else:
                            st.info("No alert files found")
                    else:
                        st.info("No alerts directory found")
                
                with sample_tabs[1]:
                    analytics_path = os.path.join(export_dir, "analytics")
                    if os.path.exists(analytics_path):
                        analytics_files = [f for f in os.listdir(analytics_path) if f.endswith('.json')]
                        if analytics_files:
                            latest_analytics = max(analytics_files, key=lambda x: os.path.getctime(os.path.join(analytics_path, x)))
                            try:
                                with open(os.path.join(analytics_path, latest_analytics), 'r') as f:
                                    analytics_data = json.load(f)
                                st.json(list(analytics_data.keys()) if isinstance(analytics_data, dict) else analytics_data[:3])
                            except Exception as e:
                                st.error(f"Error reading analytics: {e}")
                        else:
                            st.info("No analytics files found")
                    else:
                        st.info("No analytics directory found")
                
                with sample_tabs[2]:
                    plots_path = os.path.join(export_dir, "plots")
                    if os.path.exists(plots_path):
                        plots_files = [f for f in os.listdir(plots_path) if f.endswith('.json')]
                        if plots_files:
                            latest_plots = max(plots_files, key=lambda x: os.path.getctime(os.path.join(plots_path, x)))
                            try:
                                with open(os.path.join(plots_path, latest_plots), 'r') as f:
                                    plots_data = json.load(f)
                                if 'potential_returns' in plots_data:
                                    st.json(list(plots_data['potential_returns'][:3]) if isinstance(plots_data['potential_returns'], list) else plots_data['potential_returns'])
                                else:
                                    st.json(plots_data)
                            except Exception as e:
                                st.error(f"Error reading plots: {e}")
                        else:
                            st.info("No plots files found")
                    else:
                        st.info("No plots directory found")
                
                with sample_tabs[3]:
                    summary_path = os.path.join(export_dir, "summary")
                    if os.path.exists(summary_path):
                        summary_files = [f for f in os.listdir(summary_path) if f.endswith('.json')]
                        if summary_files:
                            latest_summary = max(summary_files, key=lambda x: os.path.getctime(os.path.join(summary_path, x)))
                            try:
                                with open(os.path.join(summary_path, latest_summary), 'r') as f:
                                    summary_data = json.load(f)
                                st.json(summary_data)
                            except Exception as e:
                                st.error(f"Error reading summary: {e}")
                        else:
                            st.info("No summary files found")
                    else:
                        st.info("No summary directory found")
                
                with sample_tabs[4]:
                    manifest_files = [f for f in os.listdir(export_dir) if f.startswith('manifest_') and f.endswith('.json')]
                    if manifest_files:
                        latest_manifest = max(manifest_files, key=lambda x: os.path.getctime(os.path.join(export_dir, x)))
                        try:
                            with open(os.path.join(export_dir, latest_manifest), 'r') as f:
                                manifest_data = json.load(f)
                            st.json(manifest_data)
                        except Exception as e:
                            st.error(f"Error reading manifest: {e}")
                    else:
                        st.info("No manifest files found")
            else:
                st.warning("No export files found")
        else:
            st.error("Export directory not found")
        
        st.markdown("---")
        
        # Show data structure for Docker
        st.markdown("### 📊 Data Structure for Docker")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Sample Data Entry:**")
            if results and isinstance(results, list) and len(results) > 0:
                sample_entry = results[0]
                st.json(sample_entry)
            elif results and isinstance(results, dict):
                st.json(results)
            else:
                st.text("No data available")
        
        with col2:
            st.markdown("**Data Summary:**")
            if isinstance(results, list):
                st.text(f"Total entries: {len(results)}")
                if results and len(results) > 0:
                    st.text(f"Keys in each entry: {list(results[0].keys())}")
                    if 'signal' in results[0]:
                        signals = [r.get('signal', 'N/A') for r in results]
                        signal_counts = pd.Series(signals).value_counts()
                        st.text(f"Signal distribution: {dict(signal_counts)}")
            elif isinstance(results, dict):
                st.text(f"Dictionary with keys: {list(results.keys())}")
            else:
                st.text(f"Data type: {type(results)}")
        
        st.markdown("---")
        
        # Convert to DataFrame
        if isinstance(results, list):
            results_df = pd.DataFrame(results)
        else:
            st.error("Results data is not in the expected list format")
            st.stop()
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Assets", summary['total_assets'])
        
        with col2:
            st.metric("BUY Signals", summary['buy_signals'], 
                     delta=f"{summary['buy_signals']/summary['total_assets']*100:.1f}%")
        
        with col3:
            st.metric("SELL Signals", summary['sell_signals'],
                     delta=f"{summary['sell_signals']/summary['total_assets']*100:.1f}%")
        
        with col4:
            st.metric("HOLD Signals", summary['hold_signals'],
                     delta=f"{summary['hold_signals']/summary['total_assets']*100:.1f}%")
        
        # Return metrics
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Avg Potential Return", f"{summary['avg_potential_return']:.2f}%")
        
        with col2:
            st.metric("Avg Total Return", f"{summary['avg_total_return']:.2f}%")
        
        # Results table
        st.markdown("### 📋 Analysis Results")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        
        with col1:
            signal_filter = st.selectbox("Filter by Signal", ["All", "BUY", "SELL", "HOLD"])
        
        with col2:
            min_potential = st.number_input("Min Potential Return %", value=0.0, step=0.1)
        
        with col3:
            sort_by = st.selectbox("Sort by", ["symbol", "signal", "potential_return", "total_return"])
        
        # Apply filters
        filtered_df = results_df.copy()
        if signal_filter != "All":
            filtered_df = filtered_df[filtered_df['signal'] == signal_filter]
        
        filtered_df = filtered_df[filtered_df['potential_return'] >= min_potential]
        filtered_df = filtered_df.sort_values(sort_by, ascending=False)
        
        # Display table - only show columns that exist
        available_columns = [col for col in ['symbol', 'signal', 'current_price', 'potential_return'] if col in filtered_df.columns]
        
        # Add parameter columns if they exist
        if 'degree' in filtered_df.columns:
            available_columns.extend(['degree', 'kstd'])
        if 'lookback' in filtered_df.columns:
            available_columns.append('lookback')
        if 'data_points' in filtered_df.columns:
            available_columns.append('data_points')
        if 'total_available' in filtered_df.columns:
            available_columns.append('total_available')
        if 'use_lookback' in filtered_df.columns:
            available_columns.append('use_lookback')
        
        st.dataframe(
            filtered_df[available_columns],
            use_container_width=True
        )
        
        # Charts
        st.markdown("### 📊 Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            signal_chart = create_signal_distribution(results_df)
            if signal_chart:
                st.plotly_chart(signal_chart, use_container_width=True)
        
        with col2:
            return_chart = create_return_analysis(results_df)
            if return_chart:
                st.plotly_chart(return_chart, use_container_width=True)
        
        # Signal Cards Section
        st.markdown("### 🎯 Trading Signals")
        
        # Filter signals for display
        signal_filter_display = st.multiselect(
            "Show Signals",
            options=["BUY", "SELL", "HOLD"],
            default=["BUY", "SELL"],
            key="signal_display_filter"
        )
        
        # Filter results for display
        display_signals = results_df[results_df['signal'].isin(signal_filter_display)]
        display_signals = display_signals.sort_values('potential_return', ascending=False)
        
        if not display_signals.empty:
            st.subheader(f"Trading Signals ({len(display_signals)} signals)")
            
            # Create signal tiles - 4 per row
            for i in range(0, len(display_signals), 4):
                cols = st.columns(4)
                
                for j in range(4):
                    if i + j < len(display_signals):
                        signal = display_signals.iloc[i + j]
                        with cols[j]:
                            # Determine color based on signal
                            bg_color = "#e6ffe6" if signal["signal"] == "BUY" else "#ffe6e6" if signal["signal"] == "SELL" else "#f0f0f0"
                            border_color = "green" if signal["signal"] == "BUY" else "red" if signal["signal"] == "SELL" else "gray"
                            
                            # Create tile with custom HTML/CSS
                            st.markdown(f"""
                            <div style="
                                border: 2px solid {border_color};
                                border-radius: 10px;
                                padding: 10px;
                                margin-bottom: 15px;
                                background-color: {bg_color};
                            ">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <h3 style="margin: 0; font-size: 16px; color: {border_color};">{signal["symbol"]}</h3>
                                    <span style="background-color: {border_color}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">{signal["signal"]}</span>
                                </div>
                                <div style="color: #555; font-size: 12px; margin-top: 2px;">Crypto</div>
                                <div style="display: flex; justify-content: space-between; margin-top: 8px; color: black;">
                                    <div>Price:</div>
                                    <div><b style="color: black;">${signal["current_price"]:.2f}</b></div>
                                </div>
                                <div style="display: flex; justify-content: space-between; color: black;">
                                    <div>Potential:</div>
                                    <div><b style="color: black;">{signal["potential_return"]:.2f}%</b></div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
        else:
            st.info("No signals match your filter criteria.")
        
        # Analytics and Performance Section
        st.markdown("### 📊 Analytics & Performance")
        
        # Performance metrics in cards
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Top performer
            top_performer = results_df.loc[results_df['potential_return'].idxmax()]
            st.metric(
                "Top Performer",
                top_performer['symbol'],
                f"{top_performer['potential_return']:.2f}%",
                help="Asset with highest potential return"
            )
        
        with col2:
            # Best BUY signal
            buy_signals = results_df[results_df['signal'] == 'BUY']
            if not buy_signals.empty:
                best_buy = buy_signals.loc[buy_signals['potential_return'].idxmax()]
                st.metric(
                    "Best BUY Signal",
                    best_buy['symbol'],
                    f"{best_buy['potential_return']:.2f}%",
                    help="BUY signal with highest potential return"
                )
            else:
                st.metric("Best BUY Signal", "None", "0%")
        
        with col3:
            # Best SELL signal
            sell_signals = results_df[results_df['signal'] == 'SELL']
            if not sell_signals.empty:
                best_sell = sell_signals.loc[sell_signals['potential_return'].idxmax()]
                st.metric(
                    "Best SELL Signal",
                    best_sell['symbol'],
                    f"{best_sell['potential_return']:.2f}%",
                    help="SELL signal with highest potential return"
                )
            else:
                st.metric("Best SELL Signal", "None", "0%")
        
        with col4:
            # Average potential return
            avg_return = results_df['potential_return'].mean()
            st.metric(
                "Avg Potential Return",
                f"{avg_return:.2f}%",
                help="Average potential return across all assets"
            )
        
        # Detailed analytics
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Signal Distribution by Return Range")
            
            # Create return ranges
            results_df['return_range'] = pd.cut(
                results_df['potential_return'], 
                bins=[0, 10, 25, 50, 100, float('inf')],
                labels=['0-10%', '10-25%', '25-50%', '50-100%', '100%+']
            )
            
            # Count signals by range and type
            range_signal_counts = results_df.groupby(['return_range', 'signal']).size().unstack(fill_value=0)
            
            # Create stacked bar chart
            fig = go.Figure()
            
            for signal in ['BUY', 'SELL', 'HOLD']:
                if signal in range_signal_counts.columns:
                    fig.add_trace(go.Bar(
                        name=signal,
                        x=range_signal_counts.index,
                        y=range_signal_counts[signal],
                        marker_color={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'}[signal]
                    ))
            
            fig.update_layout(
                title="Signal Distribution by Potential Return Range",
                xaxis_title="Potential Return Range",
                yaxis_title="Number of Assets",
                barmode='stack'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Price vs Potential Return")
            
            # Create scatter plot
            fig = px.scatter(
                results_df,
                x='current_price',
                y='potential_return',
                color='signal',
                hover_data=['symbol'],
                color_discrete_map={'BUY': 'green', 'SELL': 'red', 'HOLD': 'gray'},
                title="Price vs Potential Return"
            )
            
            fig.update_layout(
                xaxis_title="Current Price ($)",
                yaxis_title="Potential Return (%)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Individual asset charts
        st.markdown("### 📈 Asset Analysis")
        
        selected_symbol = st.selectbox("Select Asset for Detailed Analysis", results_df['symbol'].tolist())
        
        if selected_symbol:
            # Use default days for chart
            chart_days = 365
            price_chart = create_price_chart(engine, selected_symbol, chart_days)
            if price_chart:
                st.plotly_chart(price_chart, use_container_width=True)
            
            # Asset details
            asset_data = results_df[results_df['symbol'] == selected_symbol].iloc[0]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Current Price", f"${asset_data['current_price']:,.2f}")
            
            with col2:
                signal_color = {"BUY": "success", "SELL": "error", "HOLD": "warning"}
                st.metric("Signal", asset_data['signal'], delta=None)
            
            with col3:
                st.metric("Potential Return", f"{asset_data['potential_return']:.2f}%")
            
            with col4:
                st.metric("Total Return", f"{asset_data['total_return']:.2f}%")
        
        # Export Files Summary
        st.markdown("### 📁 Export Files Summary")
        
        # Show all export files and their contents
        export_dir = "export_results"
        if os.path.exists(export_dir):
            export_files = [f for f in os.listdir(export_dir) if f.endswith('.json')]
            
            if export_files:
                # Group files by type
                alerts_files = [f for f in export_files if 'alerts' in f]
                analytics_files = [f for f in export_files if 'analytics' in f]
                plots_files = [f for f in export_files if 'plots' in f]
                summary_files = [f for f in export_files if 'summary' in f]
                manifest_files = [f for f in export_files if 'manifest' in f]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 File Types")
                    st.metric("Alert Files", len(alerts_files))
                    st.metric("Analytics Files", len(analytics_files))
                    st.metric("Plots Files", len(plots_files))
                    st.metric("Summary Files", len(summary_files))
                    st.metric("Manifest Files", len(manifest_files))
                
                with col2:
                    st.markdown("#### 📄 Latest Files")
                    
                    # Show latest file of each type
                    for file_type, files in [
                        ("Alerts", alerts_files),
                        ("Analytics", analytics_files),
                        ("Plots", plots_files),
                        ("Summary", summary_files),
                        ("Manifest", manifest_files)
                    ]:
                        if files:
                            latest = max(files, key=lambda x: os.path.getctime(os.path.join(export_dir, x)))
                            file_size = os.path.getsize(os.path.join(export_dir, latest))
                            st.text(f"{file_type}: {latest} ({file_size:,} bytes)")
                
                # Show file contents preview
                st.markdown("#### 📋 File Contents Preview")
                
                selected_file = st.selectbox(
                    "Select file to preview",
                    export_files,
                    index=len(export_files)-1
                )
                
                if selected_file:
                    try:
                        with open(os.path.join(export_dir, selected_file), 'r') as f:
                            file_data = json.load(f)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**File Structure:**")
                            st.json(list(file_data.keys()) if isinstance(file_data, dict) else f"List with {len(file_data)} items")
                        
                        with col2:
                            st.markdown("**Sample Data:**")
                            if isinstance(file_data, dict):
                                if 'charts_data' in file_data:
                                    st.json(file_data['charts_data'].keys())
                                elif 'results' in file_data:
                                    st.json(file_data['results'][:2] if len(file_data['results']) > 0 else [])
                                else:
                                    st.json(list(file_data.items())[:3])
                            else:
                                st.json(file_data[:2] if len(file_data) > 0 else [])
                    
                    except Exception as e:
                        st.error(f"Error reading file: {e}")
            else:
                st.warning("No export files found")
        else:
            st.error("Export directory not found")
    
    else:
        # Welcome screen
        st.markdown("""
        ### 🎯 Welcome to Crypto Engine Dashboard
        
        This dashboard provides:
        
        - **Data Visualization**: View optimization results and signals
        - **Export File Browser**: Load and examine export files
        - **Signal Analysis**: BUY/SELL/HOLD signal distribution
        - **Performance Metrics**: Return analysis and risk metrics
        - **Docker Preview**: See what data Docker containers would receive
        
        **To get started:**
        1. Select an export file from the sidebar
        2. Click "Load Selected Export" to view the data
        3. Explore the visualizations and metrics
        """)
        
        # Quick status check
        st.markdown("### 🔍 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if engine:
                st.success("✅ Engine Loaded")
            else:
                st.error("❌ Engine Failed")
        
        with col2:
            if os.path.exists(engine.db_path if engine else ""):
                st.success("✅ Database Ready")
            else:
                st.warning("⚠️ Database Not Found")
        
        with col3:
            if len(tables) > 0:
                st.success(f"✅ {len(tables)} Tables Found")
            else:
                st.warning("⚠️ No Tables Found")

if __name__ == "__main__":
    main() 
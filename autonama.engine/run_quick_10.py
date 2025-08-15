#!/usr/bin/env python3
"""
Run a quick 10-asset analysis using the custom engine (no optimization)
and export files for the Streamlit dashboard.
"""

from run_complete_optimization import CompleteOptimizationRunner


def main():
    runner = CompleteOptimizationRunner()
    runner.initialize_engine()

    # Pick top 10 symbols
    symbols = runner.engine.get_top_100_assets()[:10]
    print(f"Testing with {len(symbols)} assets: {symbols}")

    # Ensure data is present/updated quickly
    print("Updating data (may skip if up-to-date)...")
    runner.engine.update_all_data(symbols=symbols, interval='1d', days=720)

    # Run analysis WITHOUT optimization for speed
    print("Running analysis without optimization...")
    analysis_result = runner.engine.run_complete_analysis(
        symbols=symbols,
        interval='1d',
        days=720,
        optimize_all_assets=False,
        output_format='both'
    )

    # Create export files structure for dashboard/ingestion
    print("Creating export files for dashboard/ingestion...")
    ingestion_files = runner.create_docker_ingestion_files(analysis_result)
    print("Done. Files:")
    for k, v in ingestion_files.items():
        if k != 'timestamp':
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()


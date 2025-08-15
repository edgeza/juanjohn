#!/usr/bin/env python3
"""
Run a quick 100-asset analysis using the custom engine (no optimization by default).
By default, exports are skipped to keep Step 0 lightweight. Use --export to generate files.
"""

import argparse
from run_complete_optimization import CompleteOptimizationRunner


def main():
    parser = argparse.ArgumentParser(description="Quick 100-asset analysis (no optimization)")
    parser.add_argument("--export", action="store_true", help="Create export files after analysis")
    args = parser.parse_args()

    runner = CompleteOptimizationRunner()
    runner.initialize_engine()

    symbols = runner.engine.get_top_100_assets()
    print(f"Running with {len(symbols)} assets")

    print("Updating data (top 100)...")
    runner.engine.update_all_data(symbols=symbols, interval='1d', days=720)

    print("Running analysis without optimization...")
    analysis_result = runner.engine.run_complete_analysis(
        symbols=symbols,
        interval='1d',
        days=720,
        optimize_all_assets=False,
        output_format='both',
        update_data_first=False
    )

    if args.export:
        print("Creating export files for dashboard/ingestion...")
        ingestion_files = runner.create_docker_ingestion_files(analysis_result)
        print("Done. Files:")
        for k, v in ingestion_files.items():
            if k != 'timestamp':
                print(f"  {k}: {v}")
    else:
        print("Skip exports (use --export to create dashboard files)")


if __name__ == "__main__":
    main()



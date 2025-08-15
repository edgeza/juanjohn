# Data Ingestion System Update

This document describes the updated data ingestion system that replaces the basic `update_market_data` function with comprehensive data updating logic from the CLI tool.

## Overview

The data ingestion system has been upgraded to support multiple data categories and use the DuckDBDataProcessor from the simple directory. This provides more robust and comprehensive data updating capabilities.

## Changes Made

### 1. Updated `update_market_data` Function

The original function that only handled crypto symbols has been replaced with a comprehensive task that supports:

- **Multiple Categories**: crypto, forex, stock, commodity
- **Flexible Parameters**: Can update all categories or specific ones
- **Force Update Option**: Can force updates regardless of data freshness
- **Progress Reporting**: Proper Celery progress updates
- **Comprehensive Logging**: Detailed logging and error handling

### 2. New `update_single_category` Task

Added a new Celery task specifically for updating single categories:

```python
@celery_app.task(bind=True)
def update_single_category(self, category: str, force_update: bool = False)
```

### 3. Integration with DuckDBDataProcessor

The system now uses the DuckDBDataProcessor from the simple directory, providing:

- Multi-source data integration (crypto, forex, stocks, commodities)
- Efficient data processing and storage
- Smart update logic (only updates when needed unless forced)

## New Task Signatures

### update_market_data

```python
update_market_data(categories=None, force_update=False)
```

**Parameters:**
- `categories` (Optional[List[str]]): List of categories to update. If None, updates all categories.
- `force_update` (bool): Whether to force update all data regardless of freshness.

**Returns:**
```python
{
    'status': 'completed',
    'categories_processed': int,
    'total_categories': int,
    'summary': {
        'total_success': int,
        'total_failed': int,
        'total_skipped': int
    },
    'details': dict,  # Per-category statistics
    'force_update': bool
}
```

### update_single_category

```python
update_single_category(category, force_update=False)
```

**Parameters:**
- `category` (str): Category to update ('crypto', 'forex', 'stock', 'commodity')
- `force_update` (bool): Whether to force update all data regardless of freshness.

**Returns:**
```python
{
    'status': 'completed',
    'category': str,
    'stats': {
        'success': int,
        'failed': int,
        'skipped': int
    },
    'force_update': bool
}
```

## Usage Examples

### 1. Update All Categories

```python
from tasks.data_ingestion import update_market_data

# Async call
result = update_market_data.delay()

# Sync call
result = update_market_data()
```

### 2. Update Specific Categories

```python
# Update only crypto and forex
result = update_market_data.delay(categories=['crypto', 'forex'])

# Force update stocks
result = update_market_data.delay(categories=['stock'], force_update=True)
```

### 3. Update Single Category

```python
from tasks.data_ingestion import update_single_category

# Update crypto data
result = update_single_category.delay('crypto')

# Force update forex data
result = update_single_category.delay('forex', force_update=True)
```

## Testing

### Test Scripts

Two test scripts have been provided:

1. **`test_data_ingestion.py`**: Tests the data ingestion functionality without Celery
2. **`call_data_tasks.py`**: Demonstrates how to call the Celery tasks

### Running Tests

```bash
# Test imports only
python test_data_ingestion.py --import-only

# Test specific category
python test_data_ingestion.py --category crypto

# Test all categories with force update
python test_data_ingestion.py --force

# Call Celery task asynchronously
python call_data_tasks.py --category crypto --monitor

# Call Celery task synchronously
python call_data_tasks.py --sync
```

## Celery Configuration

The task is automatically scheduled in `celery_app.py`:

```python
'update-market-data': {
    'task': 'tasks.data_ingestion.update_market_data',
    'schedule': 900.0,  # Every 15 minutes
},
```

## Dependencies

The updated system requires:

1. **DuckDBDataProcessor**: From the simple directory
2. **Celery**: For task management
3. **All dependencies**: From the simple directory's requirements

## Migration Notes

### Backward Compatibility

- Legacy functions (`fetch_binance_data`, `store_market_data`) are kept for backward compatibility
- Existing API calls will continue to work
- The scheduled task will automatically use the new functionality

### Configuration

No configuration changes are required. The system will automatically:

1. Import the DuckDBDataProcessor from the simple directory
2. Use the existing Celery configuration
3. Maintain all existing logging and error handling

## Monitoring

### Progress Tracking

The tasks provide detailed progress updates:

```python
{
    'current': processed_categories,
    'total': total_categories,
    'category': current_category,
    'status': 'Processing CRYPTO'
}
```

### Logging

Comprehensive logging includes:

- Task start/completion
- Per-category processing
- Success/failure statistics
- Error details
- Overall summaries

### Error Handling

- Individual category failures don't stop the entire process
- Detailed error logging for troubleshooting
- Graceful degradation when data sources are unavailable

## Performance Considerations

- **Parallel Processing**: Categories are processed sequentially to avoid API rate limits
- **Smart Updates**: Only updates data when needed (unless forced)
- **Rate Limiting**: Built-in delays between categories
- **Memory Efficient**: Uses DuckDB for efficient data processing

## Future Enhancements

Potential improvements:

1. **Parallel Category Processing**: Process multiple categories simultaneously
2. **Custom Scheduling**: Different schedules for different categories
3. **Data Quality Checks**: Validate data before storage
4. **Retry Logic**: Automatic retry for failed updates
5. **Metrics Collection**: Detailed performance metrics

# Assets Pages Documentation

This document describes the new assets listing and details pages added to the Autonama v2 web application.

## Overview

Two new pages have been created to provide comprehensive asset viewing and analysis capabilities:

1. **Assets Listing Page** (`/assets`) - Browse and search all available financial assets
2. **Asset Details Page** (`/assets/[symbol]`) - View detailed information and candlestick charts for specific assets

## Features

### Assets Listing Page (`/assets`)

#### Key Features
- **Asset Grid Display**: Clean, card-based layout showing all available assets
- **Real-time Data**: Automatically refreshes every 30 seconds
- **Search Functionality**: Search by asset name or symbol
- **Category Filtering**: Filter by crypto, forex, stock, or commodity
- **Price Information**: Current price, 24h change, and percentage change
- **Visual Indicators**: Color-coded trend indicators (green/red)
- **Summary Statistics**: Overview cards showing total assets by category

#### Components
- **AssetCard**: Individual asset display with price and change information
- **StatCard**: Summary statistics display
- **Search Bar**: Real-time search with icon
- **Category Filter**: Dropdown for filtering by asset type

### Asset Details Page (`/assets/[symbol]`)

#### Key Features
- **Interactive Candlestick Chart**: Full-featured Plotly.js chart with zoom and pan
- **Chart Controls**: Adjustable timeframe (1m to 1d) and data points (50-500)
- **Real-time Updates**: Data refreshes every 30 seconds
- **Comprehensive Stats**: Detailed asset information in organized cards
- **Responsive Design**: Works on desktop and mobile devices
- **Navigation**: Easy back navigation to assets listing

#### Chart Features
- **Candlestick Visualization**: OHLC (Open, High, Low, Close) data display
- **Interactive Controls**: Zoom, pan, and range slider
- **Multiple Timeframes**: 1m, 5m, 15m, 1h, 4h, 1d
- **Configurable Data Points**: 50, 100, 200, or 500 data points
- **Professional Styling**: Clean, financial-grade chart appearance

#### Information Cards
- **24h Change**: Price change and percentage with trend indicators
- **Volume**: 24-hour trading volume (when available)
- **Market Cap**: Total market capitalization (when available)
- **Last Updated**: Timestamp of last data update
- **Category**: Asset classification
- **Data Points**: Number of available historical records

## Technical Implementation

### Technology Stack
- **Next.js 15**: App Router with TypeScript
- **React 19**: Latest React features
- **TanStack Query**: Data fetching and caching
- **Plotly.js**: Interactive charting library
- **Tailwind CSS**: Utility-first styling
- **Lucide React**: Modern icon library

### API Integration

#### Data Sources
```typescript
// API endpoints used
GET /api/v1/data/symbols     // Get all available assets
GET /api/v1/data/ohlc        // Get OHLC data for specific asset
```

#### Mock Data
For development and testing, comprehensive mock data is provided:
- **10 Sample Assets**: Covering all categories (crypto, forex, stock, commodity)
- **Realistic Prices**: Current market-like pricing
- **Generated OHLC Data**: 100 data points with realistic volatility
- **Complete Metadata**: Names, descriptions, market caps, volumes

### File Structure
```
src/
├── app/
│   ├── assets/
│   │   ├── page.tsx              # Assets listing page
│   │   └── [symbol]/
│   │       └── page.tsx          # Asset details page
│   ├── layout.tsx                # Updated with navigation
│   └── page.tsx                  # Updated dashboard
├── components/
│   ├── Navigation.tsx            # Main navigation component
│   └── ui/
│       └── Loading.tsx           # Loading components
└── lib/
    ├── api.ts                    # API utilities and types
    └── index.ts                  # Library exports
```

## Usage Examples

### Accessing Assets
1. **From Dashboard**: Click the "Assets" card on the main dashboard
2. **Direct URL**: Navigate to `/assets`
3. **Navigation Bar**: Click "Assets" in the top navigation

### Viewing Asset Details
1. **From Assets Page**: Click any asset card
2. **Direct URL**: Navigate to `/assets/BTC%2FUSDT` (URL-encoded symbol)
3. **Browser Navigation**: Use back/forward buttons

### Chart Interaction
1. **Zoom**: Click and drag to zoom into specific time periods
2. **Pan**: Hold and drag to move around the chart
3. **Reset**: Double-click to reset zoom
4. **Range Slider**: Use the bottom slider for quick navigation
5. **Timeframe**: Change using the dropdown controls
6. **Data Points**: Adjust the number of visible data points

## Responsive Design

### Desktop (≥1024px)
- **Full Navigation**: Complete navigation bar with all links
- **Grid Layout**: Multi-column asset grid
- **Large Charts**: Full-size interactive charts
- **Side-by-side Stats**: Statistics in organized grid

### Tablet (768px - 1023px)
- **Responsive Grid**: Adjusted column count
- **Touch-friendly**: Larger touch targets
- **Optimized Charts**: Appropriately sized charts

### Mobile (≤767px)
- **Mobile Navigation**: Collapsible hamburger menu
- **Single Column**: Stacked layout for assets
- **Touch Charts**: Mobile-optimized chart interactions
- **Vertical Stats**: Stacked information cards

## Performance Optimizations

### Data Fetching
- **TanStack Query**: Intelligent caching and background updates
- **30-second Refresh**: Automatic data updates
- **Error Handling**: Graceful fallback to mock data
- **Loading States**: Skeleton loading for better UX

### Chart Performance
- **Dynamic Import**: Plotly.js loaded only when needed
- **SSR Disabled**: Chart component excluded from server-side rendering
- **Optimized Data**: Efficient data structure for chart rendering

### Bundle Optimization
- **Code Splitting**: Pages loaded on demand
- **Tree Shaking**: Unused code eliminated
- **Dynamic Imports**: Heavy components loaded asynchronously

## Customization

### Adding New Asset Categories
1. Update the `Asset` interface in `lib/api.ts`
2. Add category to the filter dropdown
3. Update the `getCategoryColor` function
4. Add mock data for the new category

### Modifying Chart Appearance
1. Update the `layout` object in `CandlestickChart` component
2. Modify colors in the `trace` configuration
3. Adjust chart dimensions and styling

### Extending API Integration
1. Update API endpoints in `lib/api.ts`
2. Modify data transformation logic
3. Add error handling for new endpoints
4. Update TypeScript interfaces

## Future Enhancements

### Planned Features
- **Favorites System**: Save and organize favorite assets
- **Alerts**: Price and volume alerts
- **Comparison Charts**: Side-by-side asset comparison
- **Technical Indicators**: RSI, MACD, moving averages
- **Export Functionality**: Download charts and data
- **Portfolio Tracking**: Track asset holdings and performance

### Technical Improvements
- **WebSocket Integration**: Real-time price updates
- **Advanced Caching**: More sophisticated caching strategies
- **Offline Support**: Service worker for offline functionality
- **PWA Features**: Progressive web app capabilities

## Troubleshooting

### Common Issues

#### Charts Not Loading
- **Cause**: Plotly.js import issues
- **Solution**: Ensure dynamic import is working correctly
- **Check**: Browser console for JavaScript errors

#### Data Not Updating
- **Cause**: API connection issues
- **Solution**: Check network connectivity and API endpoints
- **Fallback**: Mock data should load automatically

#### Mobile Navigation Issues
- **Cause**: Touch event handling
- **Solution**: Ensure proper touch event listeners
- **Test**: Use browser dev tools mobile simulation

### Development Tips
1. **Mock Data**: Use mock data for development and testing
2. **Error Boundaries**: Implement error boundaries for better error handling
3. **Loading States**: Always provide loading feedback
4. **Responsive Testing**: Test on multiple screen sizes
5. **Performance**: Monitor bundle size and loading times

## API Requirements

For full functionality, the backend should provide:

### Required Endpoints
```typescript
GET /api/v1/data/symbols
// Returns: Asset[]

GET /api/v1/data/ohlc?symbol={symbol}&timeframe={timeframe}&limit={limit}
// Returns: AssetDetails with ohlc_data
```

### Data Formats
```typescript
interface Asset {
  symbol: string;
  name: string;
  category: 'crypto' | 'forex' | 'stock' | 'commodity';
  price: number;
  change_24h: number;
  change_percent_24h: number;
  volume_24h: number;
  market_cap?: number;
  last_updated: string;
}

interface OHLCData {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}
```

This implementation provides a solid foundation for asset viewing and analysis, with room for future enhancements and customizations.

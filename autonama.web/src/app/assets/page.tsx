'use client';

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useAssetsStore } from '@/store/assetsStore';
import { Search, Filter, Activity, ChevronLeft, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';

// Memoized AssetCard component to prevent unnecessary re-renders
const AssetCard = React.memo(({ asset }: { asset: any }) => {
  const formatVolume = (volume: number) => {
    if (volume >= 1e9) return `$${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `$${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `$${(volume / 1e3).toFixed(1)}K`;
    return `$${volume.toFixed(0)}`;
  };

  const formatPrice = (price: number) => {
    if (price >= 1) return `$${price.toFixed(2)}`;
    if (price >= 0.01) return `$${price.toFixed(4)}`;
    return `$${price.toFixed(8)}`;
  };

  const getChangeColor = (change: number) => {
    return change >= 0 ? 'text-green-500' : 'text-red-500';
  };

  const getChangeIcon = (change: number) => {
    return change >= 0 ? <TrendingUp className="h-4 w-4 text-green-500" /> : <TrendingDown className="h-4 w-4 text-red-500" />;
  };

  const getCardBorderColor = (change: number) => {
    if (change >= 0) {
      return 'border-green-200 dark:border-green-800';
    } else {
      return 'border-red-200 dark:border-red-800';
    }
  };

  return (
    <div 
      className={`rounded-lg border-2 p-6 transition-all hover:shadow-lg cursor-pointer ${getCardBorderColor(asset.change_percent_24h)}`}
      style={{ 
        borderColor: asset.change_percent_24h >= 0 ? 'var(--green-border)' : 'var(--red-border)',
        backgroundColor: 'var(--bg-secondary)' 
      }}
      onClick={() => window.open(`/assets/${encodeURIComponent(asset.symbol)}`, '_blank')}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {getChangeIcon(asset.change_percent_24h)}
            <div>
              <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
                {asset.symbol}
              </h3>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                {asset.name}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* Price and Change */}
      <div className="mb-4">
        <div className="text-2xl font-bold mb-2" style={{ color: 'var(--text-primary)' }}>
          {formatPrice(asset.price)}
        </div>
        <div className="space-y-1">
          <div className={`text-sm font-medium ${getChangeColor(asset.change_percent_24h)}`}>
            {asset.change_percent_24h >= 0 ? '+' : ''}{asset.change_percent_24h.toFixed(2)}% (24h)
          </div>
          <div className="text-xs" style={{ color: 'var(--text-secondary)' }}>
            {asset.change_24h >= 0 ? '+' : ''}{formatPrice(asset.change_24h)} change
          </div>
        </div>
      </div>
      
      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <p style={{ color: 'var(--text-secondary)' }}>Volume (24h)</p>
          <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
            {formatVolume(asset.volume_24h)}
          </p>
        </div>
        <div>
          <p style={{ color: 'var(--text-secondary)' }}>Category</p>
          <p className="font-medium" style={{ color: 'var(--text-primary)' }}>
            {asset.category || 'crypto'}
          </p>
        </div>
      </div>
      
      {/* Footer */}
      <div className="mt-4 pt-3 border-t text-xs" style={{ borderColor: 'var(--border-color)', color: 'var(--text-secondary)' }}>
        <div className="flex justify-between">
          <span>Live Data</span>
          <span>{asset.timestamp ? new Date(asset.timestamp).toLocaleTimeString() : 'Now'}</span>
        </div>
      </div>
    </div>
  );
});

AssetCard.displayName = 'AssetCard';

const AssetsPage = React.memo(() => {
  const {
    assets,
    isLoading,
    error,
    searchTerm,
    selectedCategory,
    currentPage,
    totalAssets,
    assetsPerPage,
    fetchAssets,
    setSearchTerm,
    setSelectedCategory,
    setCurrentPage,
  } = useAssetsStore();

  // Debounced search to prevent excessive API calls
  const [debouncedSearchTerm, setDebouncedSearchTerm] = useState(searchTerm);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearchTerm(searchTerm);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    // Fetch assets on component mount with pagination
    fetchAssets(currentPage, assetsPerPage);

    // Set up auto-refresh every 10 minutes
    const interval = setInterval(() => {
      fetchAssets(currentPage, assetsPerPage);
    }, 600000); // 10 minutes

    return () => clearInterval(interval);
  }, [fetchAssets, currentPage, assetsPerPage]);

  // We only support crypto assets
  const handleCategoryChange = useCallback((category: string) => {
    setSelectedCategory(category);
    setCurrentPage(1); // Reset to first page when changing category
  }, [setSelectedCategory, setCurrentPage]);

  // Memoized filtered assets to prevent recalculation
  const filteredAssets = useMemo(() => {
    return assets.filter(asset => {
      const matchesSearch = debouncedSearchTerm === '' || 
        asset.symbol.toLowerCase().includes(debouncedSearchTerm.toLowerCase()) ||
        asset.name.toLowerCase().includes(debouncedSearchTerm.toLowerCase());
      
      const matchesCategory = selectedCategory === 'all' || asset.category === selectedCategory;
      
      return matchesSearch && matchesCategory;
    });
  }, [assets, debouncedSearchTerm, selectedCategory]);

  // Calculate metrics based on filtered assets
  const metrics = useMemo(() => {
    const positiveChange = filteredAssets.filter(asset => asset.change_percent_24h > 0).length;
    const negativeChange = filteredAssets.filter(asset => asset.change_percent_24h < 0).length;
    const avgVolume = filteredAssets.length > 0 
      ? filteredAssets.reduce((sum, asset) => sum + (asset.volume_24h || 0), 0) / filteredAssets.length 
      : 0;

    return { positiveChange, negativeChange, avgVolume };
  }, [filteredAssets]);

  // Pagination handlers
  const handlePreviousPage = useCallback(() => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  }, [currentPage, setCurrentPage]);

  const handleNextPage = useCallback(() => {
    const totalPages = Math.ceil(totalAssets / assetsPerPage);
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  }, [currentPage, totalAssets, assetsPerPage, setCurrentPage]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4" style={{ color: 'var(--text-secondary)' }}>Loading assets...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500">Error: {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold transition-colors duration-300" style={{ color: 'var(--text-primary)' }}>
            Top 100 Assets by Volume
          </h1>
          <p className="mt-2 transition-colors duration-300" style={{ color: 'var(--text-secondary)' }}>
            Showing {filteredAssets.length} of {totalAssets} assets - Live market data from Binance
          </p>
        </div>
        <div className="flex items-center space-x-2 text-sm" style={{ color: 'var(--text-secondary)' }}>
          <Activity className="h-4 w-4" />
          <span>Auto-refresh: 10min</span>
        </div>
      </div>

      {/* Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="glass-effect rounded-lg p-4">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Total Assets</h3>
          <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>{totalAssets}</p>
        </div>
        <div className="glass-effect rounded-lg p-4">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Positive Change</h3>
          <p className="text-2xl font-bold text-green-500">{metrics.positiveChange}</p>
        </div>
        <div className="glass-effect rounded-lg p-4">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Negative Change</h3>
          <p className="text-2xl font-bold text-red-500">{metrics.negativeChange}</p>
        </div>
        <div className="glass-effect rounded-lg p-4">
          <h3 className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>Avg Volume</h3>
          <p className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            ${(metrics.avgVolume / 1e6).toFixed(1)}M
          </p>
        </div>
      </div>

      {/* Search and Filter */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
          <input
            type="text"
            placeholder="Search assets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border transition-colors"
            style={{ 
              backgroundColor: 'var(--bg-secondary)',
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)'
            }}
          />
        </div>
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4" style={{ color: 'var(--text-secondary)' }} />
          <select
            value={selectedCategory}
            onChange={(e) => handleCategoryChange(e.target.value)}
            className="px-3 py-2 rounded-lg border transition-colors"
            style={{ 
              backgroundColor: 'var(--bg-secondary)',
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)'
            }}
          >
            <option value="all">All Categories</option>
            <option value="crypto">Crypto Assets</option>
          </select>
        </div>
      </div>

      {/* Assets Grid */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {filteredAssets.map((asset) => (
          <AssetCard key={asset.symbol} asset={asset} />
        ))}
      </div>

      {/* Pagination */}
      {totalAssets > assetsPerPage && (
        <div className="flex items-center justify-center space-x-4 mt-8">
          <button
            onClick={handlePreviousPage}
            disabled={currentPage === 1}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors disabled:opacity-50"
            style={{ 
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)'
            }}
          >
            <ChevronLeft className="h-4 w-4" />
            <span>Previous</span>
          </button>
          
          <span className="px-4 py-2" style={{ color: 'var(--text-secondary)' }}>
            Page {currentPage} of {Math.ceil(totalAssets / assetsPerPage)}
          </span>
          
          <button
            onClick={handleNextPage}
            disabled={currentPage >= Math.ceil(totalAssets / assetsPerPage)}
            className="flex items-center space-x-2 px-4 py-2 rounded-lg border transition-colors disabled:opacity-50"
            style={{ 
              borderColor: 'var(--border-color)',
              color: 'var(--text-primary)'
            }}
          >
            <span>Next</span>
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
});

AssetsPage.displayName = 'AssetsPage';

export default AssetsPage;


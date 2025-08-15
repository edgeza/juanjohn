'use client';

import React from 'react';

interface MultiAssetDashboardProps {
  className?: string;
}

const MultiAssetDashboard: React.FC<MultiAssetDashboardProps> = ({ className }) => {
  // Temporarily disabled to fix build
  return (
    <div className={`space-y-6 ${className}`}>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Multi-Asset Dashboard</h1>
          <p className="text-muted-foreground">
            Comprehensive view of all asset classes and their performance
          </p>
        </div>
      </div>
      <div className="text-center py-8">
        <p>Multi-Asset Dashboard temporarily disabled for build</p>
      </div>
    </div>
  );
};

export default MultiAssetDashboard;

import React from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  ScatterChart, Scatter, ZAxis, Legend, AreaChart, Area
} from 'recharts';

interface SignalDistributionData {
  name: string;
  value: number;
  color: string;
}

interface ReturnDistributionData {
  range: string;
  count: number;
}

interface PriceReturnData {
  symbol: string;
  price: number;
  potential_return: number;
  signal: string;
}

interface ModernChartsProps {
  signalDistribution: { BUY: number; SELL: number; HOLD: number };
  returnDistribution: { ranges: string[]; counts: number[] };
  priceReturnData: PriceReturnData[];
  isDark: boolean;
}

const COLORS = ['#10B981', '#EF4444', '#6B7280'];

export const ModernCharts: React.FC<ModernChartsProps> = ({
  signalDistribution,
  returnDistribution,
  priceReturnData,
  isDark
}) => {
  const textColor = isDark ? '#ffffff' : '#1f2937';
  const gridColor = isDark ? '#374151' : '#e5e7eb';
  const bgColor = isDark ? '#1f2937' : '#ffffff';

  // Transform signal distribution data with validation
  const signalData: SignalDistributionData[] = [
    { name: 'BUY', value: signalDistribution.BUY || 0, color: '#10B981' },
    { name: 'SELL', value: signalDistribution.SELL || 0, color: '#EF4444' },
    { name: 'HOLD', value: signalDistribution.HOLD || 0, color: '#6B7280' }
  ].filter(item => item.value > 0);

  // Transform return distribution data with validation
  const returnData: ReturnDistributionData[] = (returnDistribution.ranges || []).map((range, index) => ({
    range,
    count: (returnDistribution.counts && returnDistribution.counts[index]) || 0
  }));

  // Transform price vs return data with validation
  const scatterData = (priceReturnData || [])
    .filter(item => 
      item && 
      typeof item.price === 'number' && 
      !isNaN(item.price) && 
      item.price > 0 &&
      typeof item.potential_return === 'number' && 
      !isNaN(item.potential_return) &&
      isFinite(item.price) &&
      isFinite(item.potential_return) &&
      item.potential_return > -1000 && // Filter out extreme negative values
      item.potential_return < 1000     // Filter out extreme positive values
    )
    .map(item => ({
      ...item,
      price: Number(item.price) || 0,
      potential_return: Number(item.potential_return) || 0,
      signalColor: item.signal === 'BUY' ? '#10B981' : item.signal === 'SELL' ? '#EF4444' : '#6B7280'
    }))
    .filter(item => item.price > 0 && item.potential_return !== 0); // Additional filter

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white dark:bg-gray-800 p-3 border border-gray-200 dark:border-gray-600 rounded-lg shadow-lg">
          <p className="font-semibold" style={{ color: textColor }}>{label}</p>
          {payload.map((entry: any, index: number) => (
            <p key={index} style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // Don't render if no data
  if (signalData.length === 0 && returnData.length === 0 && scatterData.length === 0) {
    return (
      <div className="glass-effect rounded-lg p-6">
        <h3 className="text-xl font-bold mb-4" style={{ color: textColor }}>Analytics</h3>
        <p style={{ color: textColor }}>No analytics data available. Please run optimization to generate data.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Signal Distribution */}
      {signalData.length > 0 && (
        <div className="glass-effect rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4" style={{ color: textColor }}>Signal Distribution</h3>
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={signalData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {signalData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Return Distribution */}
      {returnData.length > 0 && (
        <div className="glass-effect rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4" style={{ color: textColor }}>Return Distribution</h3>
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={returnData}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis 
                  dataKey="range" 
                  tick={{ fill: textColor }}
                  axisLine={{ stroke: gridColor }}
                />
                <YAxis 
                  tick={{ fill: textColor }}
                  axisLine={{ stroke: gridColor }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Price vs Potential Return */}
      {scatterData.length > 0 && scatterData.every(item => 
        typeof item.price === 'number' && 
        !isNaN(item.price) && 
        item.price > 0 &&
        typeof item.potential_return === 'number' && 
        !isNaN(item.potential_return) &&
        isFinite(item.price) &&
        isFinite(item.potential_return)
      ) && (
        <div className="glass-effect rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4" style={{ color: textColor }}>Price vs Potential Return</h3>
          <div style={{ width: '100%', height: '400px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis 
                  type="number" 
                  dataKey="price" 
                  name="Price" 
                  tick={{ fill: textColor }}
                  axisLine={{ stroke: gridColor }}
                  domain={['dataMin', 'dataMax']}
                />
                <YAxis 
                  type="number" 
                  dataKey="potential_return" 
                  name="Potential Return" 
                  tick={{ fill: textColor }}
                  axisLine={{ stroke: gridColor }}
                />
                <ZAxis dataKey="symbol" />
                <Tooltip 
                  content={<CustomTooltip />}
                  cursor={{ strokeDasharray: '3 3' }}
                />
                <Legend />
                <Scatter 
                  name="Assets" 
                  data={scatterData} 
                  fill="#8884d8"
                  shape="circle"
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Performance Trend */}
      {scatterData.length > 0 && (
        <div className="glass-effect rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4" style={{ color: textColor }}>Performance Trend</h3>
          <div style={{ width: '100%', height: '300px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={scatterData.slice(0, 20)}>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} />
                <XAxis 
                  dataKey="symbol" 
                  tick={{ fill: textColor }}
                  axisLine={{ stroke: gridColor }}
                />
                <YAxis 
                  tick={{ fill: textColor }}
                  axisLine={{ stroke: gridColor }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="potential_return" 
                  stroke="#3B82F6" 
                  fill="#3B82F6" 
                  fillOpacity={0.3}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
}; 
 
 
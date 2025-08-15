'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface PriceChartProps {
  symbol: string;
  data: {
    labels: string[];
    prices: number[];
    upperBand?: number[];
    lowerBand?: number[];
    signal?: string;
  };
}

export default function PriceChart({ symbol, data }: PriceChartProps) {
  // Transform data for recharts
  const chartData = data.labels.map((label, index) => ({
    date: label,
    price: data.prices[index],
    upperBand: data.upperBand?.[index],
    lowerBand: data.lowerBand?.[index],
  }));

  return (
    <div className="w-full h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.1)" />
          <XAxis 
            dataKey="date" 
            stroke="rgba(255, 255, 255, 0.7)"
            fontSize={12}
          />
          <YAxis 
            stroke="rgba(255, 255, 255, 0.7)"
            fontSize={12}
          />
          <Tooltip 
            contentStyle={{
              backgroundColor: 'rgba(0, 0, 0, 0.8)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '8px',
              color: 'white'
            }}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="price" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={false}
            name="Price"
          />
          {data.upperBand && (
            <Line 
              type="monotone" 
              dataKey="upperBand" 
              stroke="#22c55e" 
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
              name="Upper Band"
            />
          )}
          {data.lowerBand && (
            <Line 
              type="monotone" 
              dataKey="lowerBand" 
              stroke="#ef4444" 
              strokeWidth={1}
              strokeDasharray="5 5"
              dot={false}
              name="Lower Band"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
} 
 
 
import { NextRequest, NextResponse } from 'next/server';

// Mock optimization results for testing
const mockOptimizationResults = {
  'completed-task': {
    task_id: 'completed-task-12345',
    status: 'completed',
    progress: 100,
    created_at: '2025-07-22T10:00:00Z',
    completed_at: '2025-07-22T10:15:00Z',
    parameters: {
      n_trials: 20,
      n_assets: 5,
      n_cores: 4,
      n_categories: 2,
      days_back: 365
    },
    results: {
      total_return: 0.2847,
      sharpe_ratio: 1.42,
      max_drawdown: -0.0856,
      win_rate: 0.634,
      profit_factor: 1.89,
      optimized_assets: 5,
      best_parameters: {
        lookback: 45,
        std_dev: 2.1,
        atr_period: 14,
        atr_multiplier: 1.8
      },
      performance_by_asset: [
        { symbol: 'BTCUSDT', return: 0.3245, sharpe: 1.67, drawdown: -0.0923, trades: 47 },
        { symbol: 'ETHUSDT', return: 0.2891, sharpe: 1.34, drawdown: -0.1156, trades: 52 },
        { symbol: 'ADAUSDT', return: 0.1967, sharpe: 0.98, drawdown: -0.0734, trades: 38 },
        { symbol: 'SOLUSDT', return: 0.4123, sharpe: 1.89, drawdown: -0.1289, trades: 41 },
        { symbol: 'DOTUSDT', return: 0.2009, sharpe: 1.12, drawdown: -0.0678, trades: 35 }
      ],
      equity_curve: generateEquityCurve()
    }
  },
  'running-task': {
    task_id: 'running-task-67890',
    status: 'running',
    progress: 67,
    created_at: '2025-07-22T13:30:00Z',
    parameters: {
      n_trials: 15,
      n_assets: 8,
      n_cores: 2,
      n_categories: 3,
      days_back: 730
    }
  },
  'failed-task': {
    task_id: 'failed-task-11111',
    status: 'failed',
    progress: 23,
    created_at: '2025-07-22T12:00:00Z',
    parameters: {
      n_trials: 10,
      n_assets: 3,
      n_cores: 1,
      n_categories: 1,
      days_back: 365
    },
    error: 'Insufficient data for optimization. Please check data availability for the selected time period.'
  }
};

function generateEquityCurve() {
  const data = [];
  const startValue = 100000;
  let currentValue = startValue;
  const startDate = new Date('2024-01-01');
  
  for (let i = 0; i < 365; i++) {
    const date = new Date(startDate);
    date.setDate(date.getDate() + i);
    
    // Simulate realistic equity curve with some volatility
    const dailyReturn = (Math.random() - 0.45) * 0.02; // Slight positive bias
    currentValue *= (1 + dailyReturn);
    
    // Calculate drawdown from peak
    const peak = Math.max(...data.map(d => d.value), currentValue);
    const drawdown = (currentValue - peak) / peak;
    
    data.push({
      date: date.toISOString(),
      value: Math.round(currentValue),
      drawdown: drawdown
    });
  }
  
  return data;
}

export async function GET(
  request: NextRequest,
  { params }: { params: { taskId: string } }
) {
  const taskId = params.taskId;
  
  // Check if we have mock data for this task ID
  const mockResult = Object.values(mockOptimizationResults).find(
    result => result.task_id === taskId
  );
  
  if (mockResult) {
    return NextResponse.json(mockResult);
  }
  
  // For any other task ID, try to fetch from the actual API
  try {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const response = await fetch(`${apiUrl}/v1/autonama/optimize/status/${taskId}`);
    
    if (response.ok) {
      const data = await response.json();
      return NextResponse.json(data);
    } else {
      // Return a generic running task for demo purposes
      return NextResponse.json({
        task_id: taskId,
        status: 'running',
        progress: Math.floor(Math.random() * 80) + 10,
        created_at: new Date().toISOString(),
        parameters: {
          n_trials: 10,
          n_assets: 5,
          n_cores: 4,
          n_categories: 2,
          days_back: 365
        }
      });
    }
  } catch (error) {
    console.error('Error fetching optimization status:', error);
    
    // Return error response
    return NextResponse.json(
      { error: 'Failed to fetch optimization status' },
      { status: 500 }
    );
  }
}

// Export the mock results for easy access in development
export const MOCK_TASK_IDS = {
  COMPLETED: 'completed-task-12345',
  RUNNING: 'running-task-67890',
  FAILED: 'failed-task-11111'
};
'use client';

export function MetricsCards() {
  const metrics = [
    { name: 'Total Return', value: '15.2%', change: '+2.1%', positive: true },
    { name: 'Sharpe Ratio', value: '1.24', change: '+0.15', positive: true },
    { name: 'Max Drawdown', value: '-8.3%', change: '-1.2%', positive: false },
    { name: 'Win Rate', value: '64.5%', change: '+3.2%', positive: true },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {metrics.map((metric) => (
        <div key={metric.name} className="card">
          <h3 className="text-sm font-medium text-gray-500">{metric.name}</h3>
          <div className="mt-2 flex items-baseline">
            <p className="text-2xl font-semibold text-gray-900">{metric.value}</p>
            <p className={`ml-2 text-sm font-medium ${
              metric.positive ? 'text-success-600' : 'text-danger-600'
            }`}>
              {metric.change}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}

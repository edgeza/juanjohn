'use client';

interface ChartContainerProps {
  title: string;
}

export function ChartContainer({ title }: ChartContainerProps) {
  return (
    <div className="card">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="h-64 bg-gray-100 rounded-md flex items-center justify-center">
        <p className="text-gray-500">Chart visualization coming soon...</p>
      </div>
    </div>
  );
}

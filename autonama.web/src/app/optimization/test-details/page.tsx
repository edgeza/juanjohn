'use client';

import Link from 'next/link';
import { CheckCircle, Clock, AlertCircle, Play } from 'lucide-react';

const MOCK_TASK_IDS = {
  COMPLETED: 'completed-task-12345',
  RUNNING: 'running-task-67890',
  FAILED: 'failed-task-11111'
};

export default function TestOptimizationDetailsPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-4xl">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Test Optimization Details</h1>
          <p className="mt-2 text-gray-600">
            Click on any of the mock optimization results below to test the details page
          </p>
        </div>

        <div className="space-y-4">
          {/* Completed Optimization */}
          <Link 
            href={`/optimization/details/${MOCK_TASK_IDS.COMPLETED}`}
            className="block rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <CheckCircle className="h-6 w-6 text-green-600" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Completed Optimization</h3>
                  <p className="text-sm text-gray-600">
                    Task ID: {MOCK_TASK_IDS.COMPLETED.slice(0, 8)}...
                  </p>
                  <p className="text-sm text-gray-500">
                    20 trials × 5 assets • 28.47% return • 1.42 Sharpe ratio
                  </p>
                </div>
              </div>
              <span className="inline-block rounded-full bg-green-100 px-3 py-1 text-sm font-medium text-green-800">
                COMPLETED
              </span>
            </div>
          </Link>

          {/* Running Optimization */}
          <Link 
            href={`/optimization/details/${MOCK_TASK_IDS.RUNNING}`}
            className="block rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Running Optimization</h3>
                  <p className="text-sm text-gray-600">
                    Task ID: {MOCK_TASK_IDS.RUNNING.slice(0, 8)}...
                  </p>
                  <p className="text-sm text-gray-500">
                    15 trials × 8 assets • Progress: ~67%
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-24 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full w-2/3"></div>
                </div>
                <span className="inline-block rounded-full bg-blue-100 px-3 py-1 text-sm font-medium text-blue-800">
                  RUNNING
                </span>
              </div>
            </div>
          </Link>

          {/* Failed Optimization */}
          <Link 
            href={`/optimization/details/${MOCK_TASK_IDS.FAILED}`}
            className="block rounded-lg border border-gray-200 bg-white p-6 shadow-sm hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertCircle className="h-6 w-6 text-red-600" />
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Failed Optimization</h3>
                  <p className="text-sm text-gray-600">
                    Task ID: {MOCK_TASK_IDS.FAILED.slice(0, 8)}...
                  </p>
                  <p className="text-sm text-gray-500">
                    10 trials × 3 assets • Failed at 23%
                  </p>
                </div>
              </div>
              <span className="inline-block rounded-full bg-red-100 px-3 py-1 text-sm font-medium text-red-800">
                FAILED
              </span>
            </div>
          </Link>
        </div>

        <div className="mt-8 rounded-lg bg-blue-50 p-6">
          <div className="flex items-start gap-3">
            <Play className="h-6 w-6 text-blue-600 mt-1" />
            <div>
              <h3 className="text-lg font-semibold text-blue-900">How to Test</h3>
              <ul className="mt-2 space-y-1 text-sm text-blue-800">
                <li>• Click on the <strong>Completed Optimization</strong> to see full results with charts and metrics</li>
                <li>• Click on the <strong>Running Optimization</strong> to see real-time progress updates</li>
                <li>• Click on the <strong>Failed Optimization</strong> to see error handling</li>
                <li>• Use the export button on completed optimizations to download results</li>
                <li>• Test the refresh functionality to simulate real-time updates</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link 
            href="/optimization"
            className="inline-flex items-center gap-2 rounded-lg bg-gray-600 px-4 py-2 text-white hover:bg-gray-700"
          >
            ← Back to Optimization Page
          </Link>
        </div>
      </div>
    </div>
  );
}
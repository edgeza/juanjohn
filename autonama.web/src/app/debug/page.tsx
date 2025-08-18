'use client';

import { useEffect, useState } from 'react';
import { getEnvironmentInfo, getPublicApiBase } from '@/lib/runtimeEnv';

export default function DebugPage() {
  const [envInfo, setEnvInfo] = useState<any>(null);
  const [apiTest, setApiTest] = useState<any>(null);

  useEffect(() => {
    // Get environment info
    const info = getEnvironmentInfo();
    setEnvInfo(info);

    // Test API connection
    const testApi = async () => {
      try {
        const apiUrl = getPublicApiBase();
        const response = await fetch(`${apiUrl}/health`);
        const data = await response.json();
        setApiTest({ success: true, data });
      } catch (error) {
        setApiTest({ success: false, error: error.message });
      }
    };

    testApi();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Environment Debug</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Environment Info */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Environment Detection</h2>
            {envInfo && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="font-medium">Mode:</span>
                  <span className={`px-2 py-1 rounded text-sm ${
                    envInfo.isDevelopment 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-blue-100 text-blue-800'
                  }`}>
                    {envInfo.isDevelopment ? 'Development' : 'Production'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Hostname:</span>
                  <span className="text-gray-600">{envInfo.hostname}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">Protocol:</span>
                  <span className="text-gray-600">{envInfo.protocol}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">API URL:</span>
                  <span className="text-gray-600 break-all">{envInfo.apiUrl}</span>
                </div>
                <div className="flex justify-between">
                  <span className="font-medium">WebSocket URL:</span>
                  <span className="text-gray-600 break-all">{envInfo.wsUrl}</span>
                </div>
              </div>
            )}
          </div>

          {/* API Test */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">API Connection Test</h2>
            {apiTest && (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="font-medium">Status:</span>
                  <span className={`px-2 py-1 rounded text-sm ${
                    apiTest.success 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {apiTest.success ? 'Connected' : 'Failed'}
                  </span>
                </div>
                {apiTest.success ? (
                  <div className="bg-gray-50 p-3 rounded">
                    <pre className="text-sm text-gray-700">
                      {JSON.stringify(apiTest.data, null, 2)}
                    </pre>
                  </div>
                ) : (
                  <div className="bg-red-50 p-3 rounded">
                    <p className="text-sm text-red-700">{apiTest.error}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Instructions */}
          <div className="lg:col-span-2 bg-blue-50 rounded-lg p-6">
            <h2 className="text-xl font-semibold mb-4 text-blue-900">How It Works</h2>
            <div className="space-y-2 text-blue-800">
              <p><strong>Local Development:</strong> When you access the app via localhost, 127.0.0.1, or local IP (192.168.x.x), it automatically uses <code>http://localhost:8000</code> for the API.</p>
              <p><strong>Server Production:</strong> When you access the app via the server IP (129.232.243.210), it automatically uses <code>http://129.232.243.210:8000</code> for the API.</p>
              <p><strong>Environment Variables:</strong> You can override this behavior by setting <code>NEXT_PUBLIC_API_URL</code> and <code>NEXT_PUBLIC_WS_URL</code>.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

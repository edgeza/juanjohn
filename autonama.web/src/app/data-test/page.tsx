'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api';
import { getPublicApiBase } from '@/lib/runtimeEnv';

export default function DataTestPage() {
  const [assets, setAssets] = useState<any[]>([]);
  const [ohlcData, setOhlcData] = useState<any[]>([]);
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionTest, setConnectionTest] = useState<any>(null);
  const [apiUrl, setApiUrl] = useState<string>('');

  useEffect(() => {
    // Get API URL once on component mount
    const getApiUrl = async () => {
      try {
        const url = getPublicApiBase();
        setApiUrl(url);
      } catch (error) {
        setApiUrl(process.env.NEXT_PUBLIC_API_URL || 'http://129.232.243.210:8000');
      }
    };
    getApiUrl();
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Test direct API connection first
        console.log('Testing API connection...');
        const apiBase = getPublicApiBase();
        const directTest = await fetch(`${apiBase}/v1/data/health`);
        const directResult = await directTest.json();
        setConnectionTest({
          status: 'success',
          data: directResult,
          message: 'Direct API connection successful'
        });
        
        // Test health check through our API client
        console.log('Testing health check...');
        const health = await apiClient.healthCheck();
        setHealthStatus(health);
        
        // Test assets
        console.log('Testing assets...');
        const assetsData = await apiClient.getAssets();
        setAssets(assetsData);
        
        // Test OHLC data for BTC/USDT
        if (assetsData.length > 0) {
          console.log('Testing OHLC data...');
          const btcData = await apiClient.getAssetBySymbol('BTC/USDT');
          setOhlcData([btcData]);
        }
        
        console.log('All tests completed successfully!');
        
      } catch (err) {
        console.error('Error in data fetching:', err);
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
        setConnectionTest({
          status: 'error',
          message: err instanceof Error ? err.message : 'Unknown error'
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const refreshData = () => {
    setLoading(true);
    setError(null);
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Testing connection to TimescaleDB...</p>
          <p className="text-sm text-gray-500 mt-2">This may take a few seconds...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex justify-between items-center">
          <h1 className="text-4xl font-bold text-gray-900">
            TimescaleDB Data Connection Test
          </h1>
          <button 
            onClick={refreshData}
            className="btn btn-primary"
          >
            Refresh Test
          </button>
        </div>

        {/* Connection Test Results */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Connection Test Results</h2>
          {connectionTest ? (
            <div className="space-y-4">
              <div className="flex items-center space-x-2">
                <div className={`w-4 h-4 rounded-full ${
                  connectionTest.status === 'success' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="font-medium">
                  Status: {connectionTest.status === 'success' ? 'Connected' : 'Failed'}
                </span>
              </div>
              <p><strong>Message:</strong> {connectionTest.message}</p>
              {connectionTest.data && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p><strong>API Response:</strong></p>
                  <pre className="text-sm mt-2 overflow-x-auto">
                    {JSON.stringify(connectionTest.data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">No connection test data available</p>
          )}
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-red-800 font-semibold">Error Details</h3>
            <p className="text-red-600 mt-2">{error}</p>
            <div className="mt-4">
              <h4 className="font-medium text-red-800">Troubleshooting:</h4>
              <ul className="list-disc list-inside text-red-600 text-sm mt-2 space-y-1">
                <li>Check if API is running: <code>curl http://129.232.243.210:8000/health</code></li>
                <li>Check CORS configuration in FastAPI</li>
                <li>Verify network connectivity between frontend and API</li>
                <li>Check browser console for additional error details</li>
              </ul>
            </div>
          </div>
        )}

        {/* API Health Status */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">API Health Status</h2>
          {healthStatus ? (
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${
                  healthStatus.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                }`}></div>
                <span className="font-medium">Status: {healthStatus.status}</span>
              </div>
              {healthStatus.database && <p><strong>Database:</strong> {healthStatus.database}</p>}
              {healthStatus.total_records && (
                <p><strong>Total Records:</strong> {healthStatus.total_records.toLocaleString()}</p>
              )}
              {healthStatus.message && <p><strong>Message:</strong> {healthStatus.message}</p>}
            </div>
          ) : (
            <div className="text-yellow-600">
              <p>⚠️ No health data available - API might not be responding</p>
            </div>
          )}
        </div>

        {/* Assets Data */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">
            Assets from TimescaleDB ({assets.length} symbols)
          </h2>
          {assets.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      24h Change
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Volume 24h
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Last Updated
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {assets.map((asset, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">
                        {asset.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                        ${asset.price?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`${
                          asset.change_percent_24h >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {asset.change_percent_24h >= 0 ? '+' : ''}
                          {asset.change_percent_24h?.toFixed(2)}%
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                        {asset.volume_24h?.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-500 text-sm">
                        {new Date(asset.last_updated).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-yellow-600">
              <p>⚠️ No assets data available - check API connection</p>
            </div>
          )}
        </div>

        {/* OHLC Data Sample */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">
            BTC/USDT OHLC Data Sample (Last 10 records)
          </h2>
          {ohlcData.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Timestamp
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Open
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      High
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Low
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Close
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Volume
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {ohlcData.slice(-10).map((candle, index) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {new Date(candle.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                        ${candle.open?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-green-600">
                        ${candle.high?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-red-600">
                        ${candle.low?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-900">
                        ${candle.close?.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-500">
                        {candle.volume?.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-yellow-600">
              <p>⚠️ No OHLC data available - check API connection</p>
            </div>
          )}
        </div>

        {/* Connection Summary */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Connection Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`text-center p-4 rounded-lg ${
              connectionTest?.status === 'success' ? 'bg-green-50' : 'bg-red-50'
            }`}>
              <div className={`text-2xl font-bold ${
                connectionTest?.status === 'success' ? 'text-green-600' : 'text-red-600'
              }`}>
                {connectionTest?.status === 'success' ? '✅' : '❌'}
              </div>
              <div className="text-sm text-gray-800">Frontend</div>
              <div className="text-xs text-gray-600">React/Next.js</div>
            </div>
            <div className={`text-center p-4 rounded-lg ${
              healthStatus?.status === 'healthy' ? 'bg-blue-50' : 'bg-red-50'
            }`}>
              <div className={`text-2xl font-bold ${
                healthStatus?.status === 'healthy' ? 'text-blue-600' : 'text-red-600'
              }`}>
                {healthStatus?.status === 'healthy' ? '✅' : '❌'}
              </div>
              <div className="text-sm text-gray-800">API</div>
              <div className="text-xs text-gray-600">FastAPI</div>
            </div>
            <div className={`text-center p-4 rounded-lg ${
              healthStatus?.database === 'connected' ? 'bg-purple-50' : 'bg-red-50'
            }`}>
              <div className={`text-2xl font-bold ${
                healthStatus?.database === 'connected' ? 'text-purple-600' : 'text-red-600'
              }`}>
                {healthStatus?.database === 'connected' ? '✅' : '❌'}
              </div>
              <div className="text-sm text-gray-800">Database</div>
              <div className="text-xs text-gray-600">TimescaleDB</div>
            </div>
          </div>
          <div className="mt-4 text-center">
            {connectionTest?.status === 'success' && healthStatus?.status === 'healthy' && healthStatus?.database === 'connected' ? (
              <>
                <p className="text-green-600 font-semibold">
                  🎉 Full stack connection successful!
                </p>
                <p className="text-gray-600 text-sm">
                  Data is flowing from TimescaleDB → FastAPI → React Frontend
                </p>
              </>
            ) : (
              <>
                <p className="text-red-600 font-semibold">
                  ⚠️ Connection issues detected
                </p>
                <p className="text-gray-600 text-sm">
                  Check the error details above and troubleshooting steps
                </p>
              </>
            )}
          </div>
        </div>

        {/* Debug Information */}
        <div className="card">
          <h2 className="text-2xl font-semibold mb-4">Debug Information</h2>
          <div className="space-y-2 text-sm">
            <p><strong>Frontend URL:</strong> http://localhost:3002</p>
            <p><strong>API URL:</strong> {apiUrl}</p>
            <p><strong>API Health:</strong> /v1/data/health</p>
            <p><strong>Browser Console:</strong> Check for additional error messages</p>
            <p><strong>CORS Status:</strong> {connectionTest?.status === 'success' ? 'Working' : 'May have issues'}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

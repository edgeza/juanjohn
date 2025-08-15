import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(
  request: NextRequest,
  { params }: { params: { symbol: string } }
) {
  try {
    const symbol = decodeURIComponent(params.symbol);
    
    // Path to the ingested data for this specific asset
    const dataPath = path.join(process.cwd(), 'public', 'data', 'api', 'assets', `${symbol}.json`);
    
    // Check if the asset data file exists
    if (!fs.existsSync(dataPath)) {
      return NextResponse.json({ 
        error: `No analytics found for ${symbol}. Please run the ingestion script first.` 
      }, { status: 404 });
    }
    
    // Read and parse the asset analytics file
    const assetData = fs.readFileSync(dataPath, 'utf-8');
    const assetAnalytics = JSON.parse(assetData);

    return NextResponse.json(assetAnalytics);
  } catch (error) {
    console.error('Error fetching asset analytics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch asset analytics' }, 
      { status: 500 }
    );
  }
} 
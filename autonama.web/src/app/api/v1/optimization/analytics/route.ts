import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    // Path to the ingested data
    const dataPath = path.join(process.cwd(), 'public', 'data', 'api', 'analytics.json');
    
    // Check if the data file exists
    if (!fs.existsSync(dataPath)) {
      return NextResponse.json({ 
        error: 'No analytics data found. Please run the ingestion script first.' 
      }, { status: 404 });
    }
    
    // Read and parse the analytics file
    const analyticsData = fs.readFileSync(dataPath, 'utf-8');
    const analytics = JSON.parse(analyticsData);

    return NextResponse.json(analytics);
  } catch (error) {
    console.error('Error fetching analytics:', error);
    return NextResponse.json(
      { error: 'Failed to fetch analytics' }, 
      { status: 500 }
    );
  }
} 
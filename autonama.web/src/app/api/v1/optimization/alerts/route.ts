import { NextRequest, NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: NextRequest) {
  try {
    // Path to the ingested data
    const dataPath = path.join(process.cwd(), 'public', 'data', 'api', 'alerts.json');
    
    // Check if the data file exists
    if (!fs.existsSync(dataPath)) {
      return NextResponse.json({ 
        error: 'No alerts data found. Please run the ingestion script first.' 
      }, { status: 404 });
    }
    
    // Read and parse the alerts file
    const alertsData = fs.readFileSync(dataPath, 'utf-8');
    const alerts = JSON.parse(alertsData);

    return NextResponse.json(alerts);
  } catch (error) {
    console.error('Error fetching alerts:', error);
    return NextResponse.json(
      { error: 'Failed to fetch alerts' }, 
      { status: 500 }
    );
  }
} 
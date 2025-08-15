#!/usr/bin/env node

/**
 * Test script to verify ingested data accessibility
 */

const fs = require('fs');
const path = require('path');

function testDataAccess() {
    console.log('🔍 Testing ingested data accessibility...\n');
    
    const dataDir = path.join(__dirname, 'public', 'data');
    const apiDir = path.join(dataDir, 'api');
    
    try {
        // Test main data file
        const mainDataPath = path.join(dataDir, 'optimization_data.json');
        if (fs.existsSync(mainDataPath)) {
            const mainData = JSON.parse(fs.readFileSync(mainDataPath, 'utf-8'));
            console.log('✅ Main data file accessible');
            console.log(`   - Alerts: ${mainData.alerts?.length || 0}`);
            console.log(`   - Analytics: ${mainData.analytics?.length || 0}`);
            console.log(`   - Assets: ${mainData.assets?.length || 0}`);
        } else {
            console.log('❌ Main data file not found');
        }
        
        // Test API files
        const apiFiles = ['alerts.json', 'analytics.json', 'summary.json', 'assets.json'];
        
        for (const file of apiFiles) {
            const filePath = path.join(apiDir, file);
            if (fs.existsSync(filePath)) {
                const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
                console.log(`✅ ${file} accessible (${Array.isArray(data) ? data.length : 'object'} items)`);
            } else {
                console.log(`❌ ${file} not found`);
            }
        }
        
        // Test individual asset files
        const assetsDir = path.join(apiDir, 'assets');
        if (fs.existsSync(assetsDir)) {
            const assetFiles = fs.readdirSync(assetsDir).filter(f => f.endsWith('.json'));
            console.log(`✅ Individual asset files: ${assetFiles.length} assets`);
            
            // Test a few specific assets
            const testAssets = ['BTCUSDT.json', 'ETHUSDT.json', 'SOLUSDT.json'];
            for (const asset of testAssets) {
                const assetPath = path.join(assetsDir, asset);
                if (fs.existsSync(assetPath)) {
                    const assetData = JSON.parse(fs.readFileSync(assetPath, 'utf-8'));
                    console.log(`   - ${asset}: ${assetData.symbol} (${assetData.signal})`);
                } else {
                    console.log(`   - ${asset}: Not found`);
                }
            }
        } else {
            console.log('❌ Assets directory not found');
        }
        
        // Test manifest
        const manifestPath = path.join(dataDir, 'ingestion_manifest.json');
        if (fs.existsSync(manifestPath)) {
            const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));
            console.log('✅ Ingestion manifest accessible');
            console.log(`   - Source run: ${manifest.source_run}`);
            console.log(`   - Ingestion time: ${manifest.ingestion_time}`);
            console.log(`   - Data summary: ${JSON.stringify(manifest.data_summary)}`);
        } else {
            console.log('❌ Ingestion manifest not found');
        }
        
        console.log('\n🎉 Data accessibility test completed!');
        
    } catch (error) {
        console.error('❌ Error testing data access:', error.message);
    }
}

testDataAccess(); 
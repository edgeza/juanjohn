# Autonama Docker Setup Guide

## 🎯 Overview

This guide will help you run the complete Autonama trading system using Docker. The system includes:

- **Data Processing**: Celery workers for market data ingestion
- **Backend API**: FastAPI service for data access and optimization
- **Frontend Dashboard**: Next.js web application
- **Database**: TimescaleDB for time-series data storage
- **Cache & Queue**: Redis for caching and task queuing
- **Monitoring**: Flower for Celery task monitoring

## 🚀 Quick Start (Windows)

1. **Start the system:**
   ```cmd
   start.bat
   ```

2. **Check status:**
   ```cmd
   status.bat
   ```

3. **Stop the system:**
   ```cmd
   stop.bat
   ```

## 🚀 Quick Start (Linux/Mac)

1. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys
   ```

2. **Start the system:**
   ```bash
   docker-compose up -d
   ```

3. **Check status:**
   ```bash
   docker-compose ps
   ```

## 📋 Prerequisites

- Docker Desktop installed and running
- API keys for data providers (optional but recommended)

### API Keys Required

For full functionality, you'll need:

1. **TwelveData API Key** (Free tier available)
   - Sign up at: https://twelvedata.com/
   - Get your API key from the dashboard

2. **Binance API Key** (Optional)
   - Create at: https://www.binance.com/en/my/settings/api-management
   - Enable spot trading permissions

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# Required API Keys
TWELVEDATA_API_KEY=your_twelvedata_api_key_here
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_SECRET_KEY=your_binance_secret_key_here

# Security
SECRET_KEY=your-secret-key-change-in-production
```

### Port Configuration

| Service | Internal Port | External Port | Description |
|---------|---------------|---------------|-------------|
| Web Frontend | 3001 | 3001 | Next.js dashboard |
| API Backend | 8000 | 8000 | FastAPI REST API |
| PostgreSQL | 5432 | 15432 | TimescaleDB database |
| Redis | 6379 | 6379 | Cache and message broker |
| Flower | 5555 | 5555 | Celery monitoring |

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   API Backend   │    │  Data Service   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (Celery)      │
│   Port: 3001    │    │   Port: 8000    │    │   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │  (TimescaleDB)  │    │   (Cache/Queue) │
                       │   Port: 15432   │    │   Port: 6379    │
                       └─────────────────┘    └─────────────────┘
```

## 📊 Data Flow

1. **Data Ingestion**: Celery workers fetch market data from APIs
2. **Storage**: Data stored in TimescaleDB (time-series optimized)
3. **Analysis**: DuckDB performs analytical queries
4. **API**: FastAPI serves data to frontend
5. **Dashboard**: Next.js displays results

## 🔍 Monitoring & Debugging

### Service Status

```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f celery_worker
docker-compose logs -f web
```

### Access Points

- **Dashboard**: http://localhost:3001
- **API Documentation**: http://localhost:8000/docs
- **Celery Monitoring**: http://localhost:5555
- **Database**: localhost:15432 (user: postgres, password: postgres)

### Health Checks

All services include health checks. Monitor with:

```bash
docker-compose ps
```

Look for:
- ✅ `healthy` - Service is working properly
- ⏳ `starting` - Service is starting up
- ❌ `unhealthy` - Service has issues

## 🛠️ Common Operations

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific services
docker-compose up -d postgres redis
docker-compose up -d celery_worker celery_beat
docker-compose up -d api web
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (⚠️ deletes data)
docker-compose down -v
```

### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api
```

### Rebuilding Services

```bash
# Rebuild all services
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build api
```

## 🔧 Database Operations

### Access PostgreSQL

```bash
# Connect to database
docker-compose exec postgres psql -U postgres -d autonama

# Run migrations
docker-compose exec api alembic upgrade head

# Backup database
docker-compose exec postgres pg_dump -U postgres autonama > backup.sql
```

### Database Schema

The system uses TimescaleDB with the following main tables:

- `trading.ohlc_data` - Market price data (hypertable)
- `analytics.indicators` - Technical indicators
- `optimization.results` - Optimization results

## 🚨 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```
   Error: Port already in use
   ```
   **Solution**: Stop other services using the same ports or change ports in docker-compose.yml

2. **API Key Errors**
   ```
   Error: Invalid API key
   ```
   **Solution**: Verify API keys in .env file

3. **Database Connection Issues**
   ```
   Error: Connection refused
   ```
   **Solution**: Check if PostgreSQL container is healthy

4. **Redis Connection Issues**
   ```
   Error: Cannot connect to Redis
   ```
   **Solution**: Verify Redis container is running

### Debug Commands

```bash
# Check container status
docker-compose ps

# View service logs
docker-compose logs [service_name]

# Access container shell
docker-compose exec [service_name] bash

# Test database connection
docker-compose exec celery_worker python test_timescale_connection.py

# Check network connectivity
docker-compose exec api ping postgres
docker-compose exec api ping redis
```

### Reset Everything

```bash
# Stop and remove everything
docker-compose down -v
docker system prune -f

# Rebuild and start
docker-compose up -d --build
```

## 📈 Performance Tuning

### Resource Limits

For production, consider adding resource limits to docker-compose.yml:

```yaml
services:
  celery_worker:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

### Scaling

Scale Celery workers for better performance:

```bash
docker-compose up -d --scale celery_worker=3
```

## 🔐 Security Considerations

1. **Change Default Passwords**
   - Update PostgreSQL password in production
   - Use strong SECRET_KEY

2. **API Key Security**
   - Restrict API key permissions
   - Use environment variables for secrets

3. **Network Security**
   - Enable SSL in production
   - Restrict external access

4. **Container Security**
   - Run containers as non-root users
   - Keep base images updated

## 📝 Development

### Local Development

For development without Docker:

```bash
# Backend
cd autonama.api
pip install -r requirements.txt
uvicorn main:app --reload

# Data Service
cd autonama.data
pip install -r requirements.txt
celery -A celery_app worker --loglevel=info

# Frontend
cd autonama.web
npm install
npm run dev
```

### Adding New Services

1. Add service to `docker-compose.yml`
2. Create Dockerfile in service directory
3. Update environment variables
4. Add health checks if needed

## 📞 Support

For issues and questions:

1. Check the troubleshooting section
2. Review service logs: `docker-compose logs`
3. Verify configuration in `.env` file
4. Test individual components
5. Check Docker and Docker Compose versions

## 🎯 Next Steps

After successful startup:

1. **Configure API Keys**: Update `.env` with your API keys
2. **Explore Dashboard**: Visit http://localhost:3001
3. **Check API Docs**: Visit http://localhost:8000/docs
4. **Monitor Tasks**: Visit http://localhost:5555
5. **Start Data Ingestion**: Configure and run data collection tasks

Happy trading! 🚀 
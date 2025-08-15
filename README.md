# Autonama Trading System

A comprehensive trading system with data ingestion, analysis, optimization, and web dashboard.

## 🏗️ Architecture

The system consists of three main components:

- **autonama.api** - FastAPI backend service
- **autonama.data** - Data processing and Celery worker service
- **autonama.web** - Next.js frontend application

## 🐳 Docker Setup

### Prerequisites

- Docker and Docker Compose installed
- API keys for data providers (TwelveData, Binance)

### Quick Start

1. **Clone and navigate to the project:**
   ```bash
   cd AutonamaDash
   ```

2. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start all services:**
   ```bash
   docker-compose up -d
   ```

4. **Check service status:**
   ```bash
   docker-compose ps
   ```

### Services

| Service | Port | Description |
|---------|------|-------------|
| **Web Frontend** | 3001 | Next.js dashboard |
| **API Backend** | 8000 | FastAPI REST API |
| **PostgreSQL** | 15432 | TimescaleDB database |
| **Redis** | 6379 | Cache and message broker |
| **Flower** | 5555 | Celery monitoring |

### Access Points

- **Dashboard**: http://localhost:3001
- **API Documentation**: http://localhost:8000/docs
- **Celery Monitoring**: http://localhost:5555
- **Database**: localhost:15432 (user: postgres, password: postgres)

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

### API Keys Setup

1. **TwelveData**: Get free API key from [twelvedata.com](https://twelvedata.com/)
2. **Binance**: Create API key from [Binance](https://www.binance.com/en/my/settings/api-management)

## 🚀 Usage

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

# Stop and remove volumes
docker-compose down -v
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f celery_worker
docker-compose logs -f web
```

### Database Operations

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d autonama

# Run migrations
docker-compose exec api alembic upgrade head

# Backup database
docker-compose exec postgres pg_dump -U postgres autonama > backup.sql
```

## 📊 Monitoring

### Health Checks

All services include health checks. Monitor with:

```bash
docker-compose ps
```

### Celery Monitoring

Access Flower dashboard at http://localhost:5555 to monitor:
- Task execution
- Worker status
- Queue performance

### Logs

```bash
# Real-time logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f celery_worker
docker-compose logs -f api
```

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3001, 8000, 15432, 6379, 5555 are available
2. **API key errors**: Verify API keys in `.env` file
3. **Database connection**: Check PostgreSQL container is healthy
4. **Redis connection**: Verify Redis container is running

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
```

### Reset Everything

```bash
# Stop and remove everything
docker-compose down -v
docker system prune -f

# Rebuild and start
docker-compose up -d --build
```

## 📁 Project Structure

```
AutonamaDash/
├── docker-compose.yml          # Main Docker configuration
├── env.example                 # Environment variables template
├── autonama.api/              # FastAPI backend
├── autonama.data/             # Data processing service
└── autonama.web/              # Next.js frontend
```

## 🛠️ Development

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

## 📈 Data Flow

1. **Data Ingestion**: Celery workers fetch market data from APIs
2. **Storage**: Data stored in TimescaleDB (time-series optimized)
3. **Analysis**: DuckDB performs analytical queries
4. **API**: FastAPI serves data to frontend
5. **Dashboard**: Next.js displays results

## 🔐 Security

- Change default passwords in production
- Use strong SECRET_KEY
- Restrict API key permissions
- Enable SSL in production
- Use environment variables for secrets

## 📝 License

This project is proprietary software.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review service logs
3. Verify configuration
4. Test individual components 
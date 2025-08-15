# 🚀 AutonamaDash GitHub Migration Guide

This guide will help you migrate your AutonamaDash application to GitHub and set up a complete development environment.

## 📋 Prerequisites

Before starting the migration, ensure you have:

- [Git](https://git-scm.com/) installed and configured
- [Docker](https://www.docker.com/) and Docker Compose installed
- [GitHub account](https://github.com/) with access to the target repository
- API keys for data providers (TwelveData, Binance)

## 🔄 Migration Steps

### Step 1: Prepare Your Local Repository

1. **Clean up sensitive data** (if not already done):
   ```bash
   # Remove sensitive files that shouldn't be committed
   rm -f .env
   rm -f crypto_data.db
   rm -rf export_results/
   rm -rf results/
   rm -rf autonama.engine/cache/
   rm -rf autonama.engine/export_results/
   rm -rf autonama.engine/results/
   ```

2. **Verify .gitignore is in place**:
   ```bash
   # Ensure .gitignore exists and excludes sensitive data
   ls -la .gitignore
   ```

### Step 2: Initialize Git Repository

1. **Initialize Git** (if not already done):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: AutonamaDash trading system"
   ```

2. **Add GitHub remote**:
   ```bash
   git remote add origin https://github.com/edgeza/juanjohn.git
   git branch -M main
   ```

### Step 3: Push to GitHub

1. **Push your code**:
   ```bash
   git push -u origin main
   ```

2. **Verify on GitHub**:
   - Visit https://github.com/edgeza/juanjohn
   - Confirm all files are uploaded
   - Check that sensitive files are not visible

## 🐳 Docker Setup After Migration

### Step 1: Clone the Repository

```bash
# Clone the repository to a new location
git clone https://github.com/edgeza/juanjohn.git
cd juanjohn
```

### Step 2: Environment Configuration

1. **Copy environment template**:
   ```bash
   cp env.example .env
   ```

2. **Edit .env with your API keys**:
   ```bash
   # Edit .env file with your actual API keys
   nano .env
   # or
   code .env
   ```

3. **Required configuration**:
   ```bash
   # Minimum required settings
   TWELVEDATA_API_KEY=your_actual_twelvedata_key
   BINANCE_API_KEY=your_actual_binance_key
   BINANCE_SECRET_KEY=your_actual_binance_secret
   SECRET_KEY=your-secret-key-change-in-production
   ```

### Step 3: Start Services

1. **Start all services**:
   ```bash
   docker-compose up -d --build
   ```

2. **Check service status**:
   ```bash
   docker-compose ps
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f
   ```

## 🔧 Development Environment Setup

### Local Development (Without Docker)

1. **Backend API**:
   ```bash
   cd autonama.api
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Data Processing**:
   ```bash
   cd autonama.data
   pip install -r requirements.txt
   celery -A celery_app worker --loglevel=info
   ```

3. **Frontend**:
   ```bash
   cd autonama.web
   npm install
   npm run dev
   ```

### Database Setup

1. **Start only database services**:
   ```bash
   docker-compose up -d postgres redis
   ```

2. **Run migrations**:
   ```bash
   docker-compose exec api alembic upgrade head
   ```

3. **Verify connection**:
   ```bash
   docker-compose exec postgres psql -U postgres -d autonama -c "\dt"
   ```

## 📊 Access Points

After successful setup, access your application at:

| Service | URL | Description |
|---------|-----|-------------|
| **Web Dashboard** | http://localhost:3001 | Next.js frontend |
| **API Documentation** | http://localhost:8000/docs | FastAPI Swagger UI |
| **Celery Monitoring** | http://localhost:5555 | Flower dashboard |
| **Database** | localhost:5432 | PostgreSQL/TimescaleDB |

## 🔍 Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using the ports
   netstat -tulpn | grep :3001
   netstat -tulpn | grep :8000
   netstat -tulpn | grep :5432
   ```

2. **Docker build failures**:
   ```bash
   # Clean Docker cache
   docker system prune -f
   docker-compose build --no-cache
   ```

3. **Database connection issues**:
   ```bash
   # Check database health
   docker-compose exec postgres pg_isready -U postgres
   ```

4. **API key errors**:
   ```bash
   # Verify environment variables
   docker-compose exec api env | grep API_KEY
   ```

### Reset Everything

```bash
# Stop and remove all containers and volumes
docker-compose down -v
docker system prune -f

# Rebuild and start
docker-compose up -d --build
```

## 📁 Repository Structure

```
juanjohn/
├── .env.example              # Environment template
├── .gitignore               # Git exclusions
├── docker-compose.yml       # Docker orchestration
├── README.md                # Project documentation
├── MIGRATION_GUIDE.md       # This guide
├── autonama.api/            # FastAPI backend
├── autonama.data/           # Data processing service
├── autonama.engine/         # Trading engine
├── autonama.ingestion/      # Data ingestion
└── autonama.web/            # Next.js frontend
```

## 🔐 Security Considerations

1. **Never commit .env files** - they contain API keys
2. **Use strong SECRET_KEY** in production
3. **Restrict API key permissions** on data provider platforms
4. **Enable SSL/TLS** in production environments
5. **Regular security updates** for dependencies

## 📈 Next Steps

After successful migration:

1. **Set up CI/CD** with GitHub Actions
2. **Configure automated testing**
3. **Set up monitoring and alerting**
4. **Plan production deployment**
5. **Document API endpoints**
6. **Create user guides**

## 🤝 Support

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Review service logs: `docker-compose logs [service_name]`
3. Verify configuration in `.env` file
4. Check GitHub repository for updates
5. Create issues in the GitHub repository

## 📝 Notes

- The `.env.example` file contains all required environment variables
- Sensitive data files are automatically excluded by `.gitignore`
- Docker services include health checks for reliability
- All services are configured for development by default
- Production deployments require additional security configuration

---

**Happy Trading! 🚀📈**


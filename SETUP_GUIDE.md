# Algo Hub Financial Dashboard - Production Setup Guide

## Prerequisites
- Docker & Docker Compose
- Python 3.9+
- PostgreSQL client tools
- Redis CLI

## Environment Setup

### 1. Environment Variables
```bash
# Create .env file
cp .env.example .env
# Edit .env with your specific values
```

### 2. Database Migration
```bash
# For initial setup
python run_migrations.py

# For PostgreSQL migration (production)
python migration_scripts/postgres_migration.py
```

### 3. OCR Dependencies
```bash
# Install Tesseract OCR
# Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-pak
# macOS: brew install tesseract
# Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
```

### 4. SSL/TLS Setup (Production)
```bash
# Generate certificates
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```

## Running in Production
```bash
# Using Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# With SSL termination
docker-compose -f docker-compose.prod.yml -f docker-compose.ssl.yml up -d
```

## Monitoring & Maintenance
- Database backup: `docker exec algohub-db pg_dump -U user algohub > backup.sql`
- Performance monitoring: Use Prometheus + Grafana
- Log aggregation: ELK stack integration

## Security Configuration
- Set JWT_SECRET_KEY in environment
- Configure FERNET_KEY for encryption
- Enable SSL/TLS for all connections
- Regular security audits

## Performance Optimization
- Use Redis for caching
- Implement connection pooling
- Enable query optimization
- Set up proper indexing

## Deployment Strategies
- Blue-green deployment for zero-downtime updates
- Health checks for service discovery
- Load balancing configuration
- Backup and disaster recovery plans
# WindX Product Configurator - Azure App Service Deployment Guide

## 📋 Overview

This guide walks you through deploying the WindX Product Configurator to Azure App Service with CI/CD integration. The application is a comprehensive product configuration platform for custom manufacturing industries.

### 🏷️ Application Metadata
- **Name**: WindX Product Configurator
- **Version**: 1.0.0
- **Description**: Automated product configurator for custom manufacturing - windows, doors, furniture, and more
- **Author**: alaamer12 <ahmedmuhmmed239@gmail.com>
- **License**: MIT
- **Repository**: https://github.com/alaamer12/Windx

### 🎯 Key Features
- Dynamic product configuration with hierarchical attributes
- Real-time pricing calculations with formula engine
- Template management and quote generation
- Order management with snapshots
- Role-based access control (RBAC) with Casbin
- PostgreSQL with LTREE extension for hierarchical data
- Redis caching and rate limiting

---

## 🏗️ Prerequisites

### Azure Resources Required
1. **Azure App Service** (Linux, Python 3.11+)
2. **Azure Database for PostgreSQL** (or Supabase)
3. **Azure Cache for Redis** (Standard tier recommended)
4. **Azure Resource Group**

### Local Requirements
- Git repository with your WindX code
- Azure CLI (optional, for command-line deployment)
- Access to Azure Portal

---

## 🚀 Step-by-Step Deployment

### Step 1: Create Azure Resources

#### 1.1 Create Resource Group
```bash
# Via Azure CLI (optional)
az group create --name windx-production --location "East US"
```

Or via Azure Portal:
- Navigate to Resource Groups → Create
- Name: `windx-production`
- Region: Choose your preferred region

#### 1.2 Create Azure Database for PostgreSQL
```bash
# Via Azure CLI (optional)
az postgres server create \
  --resource-group windx-production \
  --name windx-postgres-server \
  --location "East US" \
  --admin-user windxadmin \
  --admin-password "YourSecurePassword123!" \
  --sku-name GP_Gen5_2
```

Or via Azure Portal:
- Navigate to Azure Database for PostgreSQL servers → Create
- Server name: `windx-postgres-server`
- Admin username: `windxadmin`
- Password: Use a secure password
- Pricing tier: General Purpose, 2 vCores

**Important**: Enable the `ltree` extension:
```sql
-- Connect to your database and run:
CREATE EXTENSION IF NOT EXISTS ltree;
```

#### 1.3 Create Azure Cache for Redis
```bash
# Via Azure CLI (optional)
az redis create \
  --resource-group windx-production \
  --name windx-cache \
  --location "East US" \
  --sku Standard \
  --vm-size c1
```

Or via Azure Portal:
- Navigate to Azure Cache for Redis → Create
- DNS name: `windx-cache`
- Pricing tier: Standard C1 (1 GB)

#### 1.4 Create Azure App Service
```bash
# Via Azure CLI (optional)
az appservice plan create \
  --resource-group windx-production \
  --name windx-app-plan \
  --is-linux \
  --sku B2

az webapp create \
  --resource-group windx-production \
  --plan windx-app-plan \
  --name windx-configurator \
  --runtime "PYTHON|3.11"
```

Or via Azure Portal:
- Navigate to App Services → Create
- App name: `windx-configurator`
- Runtime stack: Python 3.11
- Operating System: Linux
- App Service Plan: Create new (B2 or higher recommended)

### Step 2: Configure Environment Variables

Navigate to your App Service → Configuration → Application Settings and add these variables:

#### Core Application Settings
```
APP_NAME = WindX Product Configurator
APP_VERSION = 1.0.0
DEBUG = False
API_V1_PREFIX = /api/v1
```

#### Database Configuration
```
DATABASE_PROVIDER = postgresql
DATABASE_CONNECTION_MODE = direct
DATABASE_HOST = windx-postgres-server.postgres.database.azure.com
DATABASE_PORT = 5432
DATABASE_USER = windxadmin@windx-postgres-server
DATABASE_PASSWORD = YourSecurePassword123!
DATABASE_NAME = windx_production
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
DATABASE_POOL_PRE_PING = True
DATABASE_ECHO = False
```

#### Security Settings (⚠️ CRITICAL: Change these!)
```
SECRET_KEY = GENERATE-A-SECURE-32-CHARACTER-STRING-HERE
ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 30
```

Generate a secure secret key:
```bash
openssl rand -hex 32
```

#### CORS Configuration
```
BACKEND_CORS_ORIGINS = ["https://windx-configurator.azurewebsites.net","https://yourdomain.com"]
```

#### Redis Configuration
```
CACHE_ENABLED = True
CACHE_REDIS_HOST = windx-cache.redis.cache.windows.net
CACHE_REDIS_PORT = 6380
CACHE_REDIS_PASSWORD = YOUR_REDIS_PRIMARY_KEY
CACHE_REDIS_DB = 0
CACHE_PREFIX = windx:cache
CACHE_DEFAULT_TTL = 300

LIMITER_ENABLED = True
LIMITER_REDIS_HOST = windx-cache.redis.cache.windows.net
LIMITER_REDIS_PORT = 6380
LIMITER_REDIS_PASSWORD = YOUR_REDIS_PRIMARY_KEY
LIMITER_REDIS_DB = 1
LIMITER_PREFIX = windx:limiter
LIMITER_DEFAULT_TIMES = 100
LIMITER_DEFAULT_SECONDS = 60
```

#### WindX Configurator Settings
```
WINDX_FORMULA_MAX_LENGTH = 500
WINDX_FORMULA_TIMEOUT_SECONDS = 5
WINDX_FORMULA_ALLOWED_FUNCTIONS = abs,min,max,round,ceil,floor,sqrt,pow
WINDX_FORMULA_MAX_VARIABLES = 20
WINDX_SNAPSHOT_RETENTION_DAYS = 730
WINDX_SNAPSHOT_AUTO_CLEANUP = True
WINDX_TEMPLATE_TRACK_USAGE = True
WINDX_TEMPLATE_SUCCESS_THRESHOLD = 25
WINDX_TEMPLATE_POPULAR_LIMIT = 10
WINDX_PRICE_CALCULATION_PRECISION = 2
WINDX_WEIGHT_CALCULATION_PRECISION = 2
```

### Step 3: Configure Startup Command

Navigate to App Service → Configuration → General Settings:

**Startup Command**:
```bash
/home/site/wwwroot/scripts/startup-azure.sh
```

Make sure the startup script is executable by adding this to your repository:
```bash
chmod +x scripts/startup-azure.sh
```

### Step 4: Set Up CI/CD

#### Option A: GitHub Actions (Recommended)

1. Navigate to App Service → Deployment Center
2. Choose "GitHub" as source
3. Authorize Azure to access your GitHub account
4. Select your repository and branch
5. Azure will automatically create a GitHub Actions workflow

The workflow will be created at `.github/workflows/main_windx-configurator.yml`

#### Option B: Azure DevOps

1. Navigate to App Service → Deployment Center
2. Choose "Azure Repos" as source
3. Configure your Azure DevOps project and repository

### Step 5: Database Setup

After deployment, you need to set up the database:

#### 5.1 Run Migrations
The startup script automatically runs migrations, but you can also run them manually:

```bash
# Via Azure CLI
az webapp ssh --resource-group windx-production --name windx-configurator

# Inside the container
cd /home/site/wwwroot
uv run alembic upgrade head
```

#### 5.2 Seed Initial Data
```bash
# Inside the container
uv run python manage.py create_superuser
uv run python manage.py seed_data
```

---

## 🔧 Configuration Details

### Startup Script Features

The `scripts/startup-azure.sh` script automatically:
- Installs UV package manager
- Installs production dependencies
- Sets up Redis (if not using Azure Redis Cache)
- Runs database migrations
- Starts the application with Gunicorn

### Application Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Azure App     │    │  Azure Database  │    │  Azure Cache    │
│   Service       │◄──►│  for PostgreSQL  │    │  for Redis      │
│                 │    │                  │    │                 │
│  - FastAPI      │    │  - LTREE ext.    │    │  - Caching      │
│  - Gunicorn     │    │  - Hierarchical  │    │  - Rate Limit   │
│  - 4 Workers    │    │    Data          │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Performance Recommendations

#### App Service Plan Sizing
- **Development**: B1 (1 vCore, 1.75 GB RAM)
- **Production**: B2+ (2+ vCores, 3.5+ GB RAM)
- **High Traffic**: P2V2+ (2+ vCores, 7+ GB RAM)

#### Database Sizing
- **Development**: Basic (1 vCore, 2 GB RAM)
- **Production**: General Purpose (2+ vCores, 5+ GB RAM)
- **High Performance**: Memory Optimized (4+ vCores, 20+ GB RAM)

#### Redis Sizing
- **Development**: Basic C0 (250 MB)
- **Production**: Standard C1+ (1+ GB)
- **High Performance**: Premium P1+ (6+ GB)

---

## 🔍 Monitoring & Troubleshooting

### Health Check Endpoint

The application provides a comprehensive health check:
```
GET https://windx-configurator.azurewebsites.net/health
```

Response includes:
- Overall application status
- Database connectivity
- Redis cache status
- Redis rate limiter status

### Log Monitoring

#### Application Logs
```bash
# Via Azure CLI
az webapp log tail --resource-group windx-production --name windx-configurator
```

Or via Azure Portal:
- Navigate to App Service → Monitoring → Log stream

#### Application Insights (Recommended)
1. Create Application Insights resource
2. Connect to your App Service
3. Monitor performance, errors, and usage

### Common Issues & Solutions

#### Issue: Database Connection Fails
**Solution**: 
- Check firewall rules in Azure Database for PostgreSQL
- Verify connection string format
- Ensure LTREE extension is installed

#### Issue: Redis Connection Fails
**Solution**:
- Verify Redis cache is running
- Check access keys and connection string
- Ensure SSL is enabled (port 6380)

#### Issue: Startup Script Fails
**Solution**:
- Check startup script permissions: `chmod +x scripts/startup-azure.sh`
- Review application logs for specific errors
- Verify all environment variables are set

#### Issue: Static Files Not Loading
**Solution**:
- Ensure static files are included in deployment
- Check CORS settings for static file domains
- Verify static file paths in application

---

## 🔒 Security Considerations

### Environment Variables
- Never commit sensitive values to repository
- Use Azure Key Vault for production secrets
- Rotate keys regularly

### Database Security
- Enable SSL connections
- Use strong passwords
- Restrict network access
- Regular security updates

### Application Security
- Keep dependencies updated
- Monitor for vulnerabilities
- Use HTTPS only
- Implement proper CORS policies

---

## 📊 Scaling & Performance

### Horizontal Scaling
```bash
# Scale out to multiple instances
az appservice plan update --resource-group windx-production --name windx-app-plan --number-of-workers 3
```

### Vertical Scaling
```bash
# Scale up to higher tier
az appservice plan update --resource-group windx-production --name windx-app-plan --sku P2V2
```

### Database Scaling
- Use read replicas for read-heavy workloads
- Consider connection pooling
- Monitor and optimize queries

### Caching Strategy
- Enable Redis caching for frequently accessed data
- Use appropriate TTL values
- Monitor cache hit rates

---

## 🚀 Post-Deployment Checklist

- [ ] Application starts successfully
- [ ] Health check endpoint returns "healthy"
- [ ] Database connection works
- [ ] Redis cache is functional
- [ ] Admin interface is accessible
- [ ] API documentation is available at `/redoc`
- [ ] CORS is properly configured
- [ ] SSL certificate is valid
- [ ] Monitoring is set up
- [ ] Backup strategy is in place

---

## 📞 Support & Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Azure App Service Documentation](https://docs.microsoft.com/en-us/azure/app-service/)
- [PostgreSQL LTREE Documentation](https://www.postgresql.org/docs/current/ltree.html)

### WindX Specific
- Repository: https://github.com/alaamer12/Windx
- Issues: https://github.com/alaamer12/Windx/issues
- Author: alaamer12 <ahmedmuhmmed239@gmail.com>

### Azure Support
- [Azure Support Plans](https://azure.microsoft.com/en-us/support/plans/)
- [Azure Community Support](https://docs.microsoft.com/en-us/answers/products/azure)

---

## 📝 License

This deployment guide is part of the WindX Product Configurator project, licensed under the MIT License.

Copyright (c) 2024 alaamer12

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
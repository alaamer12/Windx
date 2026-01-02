# WindX Product Configurator - Azure Deployment Checklist

## 📋 Pre-Deployment Checklist

### 🏗️ Azure Resources
- [ ] **Resource Group** created (`windx-production`)
- [ ] **Azure Database for PostgreSQL** created and configured
  - [ ] LTREE extension enabled: `CREATE EXTENSION IF NOT EXISTS ltree;`
  - [ ] Firewall rules configured to allow Azure services
  - [ ] Admin user created with strong password
- [ ] **Azure Cache for Redis** created (Standard tier or higher)
  - [ ] Access keys obtained
  - [ ] SSL enabled (port 6380)
- [ ] **Azure App Service** created
  - [ ] Linux OS selected
  - [ ] Python 3.11 runtime configured
  - [ ] B2 or higher pricing tier selected

### 🔐 Security Configuration
- [ ] **Secret Key** generated (32+ characters): `openssl rand -hex 32`
- [ ] **Database Password** is strong and secure
- [ ] **Redis Access Keys** obtained from Azure Portal
- [ ] **Environment Variables** configured in App Service settings
- [ ] **CORS Origins** updated with production URLs
- [ ] **SSL Certificate** configured (automatic with *.azurewebsites.net)

### 📁 Repository Setup
- [ ] **Startup Script** is executable: `chmod +x scripts/startup-azure.sh`
- [ ] **Environment Files** are NOT committed to repository
- [ ] **Dependencies** are up to date in `pyproject.toml`
- [ ] **Database Migrations** are ready: `alembic upgrade head`

---

## 🚀 Deployment Steps

### Step 1: Environment Configuration
- [ ] Navigate to App Service → Configuration → Application Settings
- [ ] Add all required environment variables from `.env.azure`
- [ ] Verify database connection string format
- [ ] Test Redis connection parameters
- [ ] Save configuration changes

### Step 2: Startup Command
- [ ] Navigate to App Service → Configuration → General Settings
- [ ] Set Startup Command: `/home/site/wwwroot/scripts/startup-azure.sh`
- [ ] Save configuration

### Step 3: CI/CD Setup
- [ ] Navigate to App Service → Deployment Center
- [ ] Choose GitHub as source
- [ ] Authorize Azure to access GitHub account
- [ ] Select repository and branch (`main` or `production`)
- [ ] Azure creates GitHub Actions workflow automatically
- [ ] Verify workflow file is created in `.github/workflows/`

### Step 4: Initial Deployment
- [ ] Push code to configured branch
- [ ] Monitor GitHub Actions workflow execution
- [ ] Check deployment logs in Azure Portal
- [ ] Verify application starts successfully

---

## ✅ Post-Deployment Verification

### 🔍 Health Checks
- [ ] **Application Status**: Visit `https://your-app.azurewebsites.net/`
- [ ] **Health Endpoint**: Check `https://your-app.azurewebsites.net/health`
  - [ ] Overall status: "healthy"
  - [ ] Database status: "healthy"
  - [ ] Cache status: "healthy"
  - [ ] Rate limiter status: "healthy"
- [ ] **API Documentation**: Access `https://your-app.azurewebsites.net/redoc`

### 🗄️ Database Verification
- [ ] **Connection**: Application can connect to PostgreSQL
- [ ] **LTREE Extension**: Verify extension is installed
- [ ] **Migrations**: All migrations applied successfully
- [ ] **Initial Data**: Seed data loaded if required

### 🔴 Redis Verification
- [ ] **Cache Connection**: Application can connect to Redis cache
- [ ] **Rate Limiter**: Rate limiting is functional
- [ ] **Performance**: Cache hit rates are reasonable

### 🔧 Application Features
- [ ] **Admin Interface**: Access admin panel
- [ ] **Authentication**: Login/logout functionality works
- [ ] **API Endpoints**: Core API endpoints respond correctly
- [ ] **Static Files**: CSS, JS, images load properly
- [ ] **CORS**: Frontend can communicate with API

---

## 🔧 Configuration Verification

### Environment Variables Checklist
```bash
# Core Application
✅ APP_NAME = "WindX Product Configurator"
✅ APP_VERSION = "1.0.0"
✅ DEBUG = False
✅ API_V1_PREFIX = "/api/v1"

# Database (PostgreSQL)
✅ DATABASE_PROVIDER = postgresql
✅ DATABASE_HOST = your-server.postgres.database.azure.com
✅ DATABASE_PORT = 5432
✅ DATABASE_USER = admin@server-name
✅ DATABASE_PASSWORD = [SECURE_PASSWORD]
✅ DATABASE_NAME = windx_production

# Security
✅ SECRET_KEY = [32_CHARACTER_SECRET]
✅ ALGORITHM = HS256
✅ ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Redis Cache
✅ CACHE_ENABLED = True
✅ CACHE_REDIS_HOST = your-cache.redis.cache.windows.net
✅ CACHE_REDIS_PORT = 6380
✅ CACHE_REDIS_PASSWORD = [REDIS_KEY]

# Rate Limiter
✅ LIMITER_ENABLED = True
✅ LIMITER_REDIS_HOST = your-cache.redis.cache.windows.net
✅ LIMITER_REDIS_PORT = 6380
✅ LIMITER_REDIS_PASSWORD = [REDIS_KEY]

# CORS
✅ BACKEND_CORS_ORIGINS = ["https://your-app.azurewebsites.net"]
```

---

## 🚨 Troubleshooting Common Issues

### Issue: Application Won't Start
**Symptoms**: 
- App Service shows "Application Error"
- Health check returns 503/500 errors

**Solutions**:
- [ ] Check Application Logs in Azure Portal
- [ ] Verify startup script permissions: `chmod +x scripts/startup-azure.sh`
- [ ] Ensure all environment variables are set
- [ ] Check Python version compatibility (3.11+)

### Issue: Database Connection Failed
**Symptoms**:
- Health check shows database status "unhealthy"
- Database-related errors in logs

**Solutions**:
- [ ] Verify database connection string format
- [ ] Check Azure PostgreSQL firewall rules
- [ ] Ensure LTREE extension is installed
- [ ] Test connection from Azure Cloud Shell

### Issue: Redis Connection Failed
**Symptoms**:
- Cache/rate limiter status "unhealthy"
- Redis connection errors in logs

**Solutions**:
- [ ] Verify Redis access keys
- [ ] Check SSL settings (use port 6380)
- [ ] Ensure Redis cache is running
- [ ] Test connection with Redis CLI

### Issue: Static Files Not Loading
**Symptoms**:
- CSS/JS files return 404 errors
- Admin interface appears unstyled

**Solutions**:
- [ ] Check static file paths in application
- [ ] Verify CORS settings for static files
- [ ] Ensure static files are included in deployment
- [ ] Check web.config static content configuration

---

## 📊 Performance Optimization

### App Service Scaling
- [ ] **Monitor CPU/Memory usage** in Azure Portal
- [ ] **Scale up** to higher tier if needed (B2 → P2V2)
- [ ] **Scale out** to multiple instances for high traffic
- [ ] **Enable Application Insights** for detailed monitoring

### Database Optimization
- [ ] **Monitor connection pool usage**
- [ ] **Optimize slow queries** using PostgreSQL logs
- [ ] **Consider read replicas** for read-heavy workloads
- [ ] **Regular maintenance** and statistics updates

### Redis Optimization
- [ ] **Monitor cache hit rates**
- [ ] **Adjust TTL values** based on usage patterns
- [ ] **Scale Redis tier** if memory usage is high
- [ ] **Use appropriate eviction policies**

---

## 🔒 Security Hardening

### Post-Deployment Security
- [ ] **Change default passwords** for all services
- [ ] **Enable Azure Security Center** recommendations
- [ ] **Configure backup strategies** for database and app
- [ ] **Set up monitoring alerts** for security events
- [ ] **Regular security updates** for dependencies
- [ ] **Implement Azure Key Vault** for sensitive secrets
- [ ] **Enable diagnostic logging** for audit trails

### Network Security
- [ ] **Configure Virtual Network** (optional, for enhanced security)
- [ ] **Set up Private Endpoints** for database (optional)
- [ ] **Enable DDoS protection** (optional, for high-traffic apps)
- [ ] **Configure Web Application Firewall** (optional)

---

## 📈 Monitoring & Maintenance

### Ongoing Monitoring
- [ ] **Set up Application Insights** for performance monitoring
- [ ] **Configure alerts** for:
  - [ ] Application errors (5xx responses)
  - [ ] High response times (>2 seconds)
  - [ ] Database connection failures
  - [ ] Redis connection failures
  - [ ] High CPU/memory usage
- [ ] **Regular health check monitoring**
- [ ] **Database performance monitoring**

### Maintenance Schedule
- [ ] **Weekly**: Review application logs and performance metrics
- [ ] **Monthly**: Update dependencies and security patches
- [ ] **Quarterly**: Review and optimize database performance
- [ ] **Annually**: Security audit and architecture review

---

## 📞 Support Contacts

### WindX Application
- **Repository**: https://github.com/alaamer12/Windx
- **Issues**: https://github.com/alaamer12/Windx/issues
- **Author**: alaamer12 <ahmedmuhmmed239@gmail.com>

### Azure Support
- **Documentation**: https://docs.microsoft.com/en-us/azure/app-service/
- **Community**: https://docs.microsoft.com/en-us/answers/products/azure
- **Support Plans**: https://azure.microsoft.com/en-us/support/plans/

---

## ✅ Final Deployment Sign-off

**Deployment Date**: _______________

**Deployed By**: _______________

**Version**: 1.0.0

**Environment**: Production

### Sign-off Checklist
- [ ] All health checks pass
- [ ] Performance is acceptable
- [ ] Security measures are in place
- [ ] Monitoring is configured
- [ ] Documentation is updated
- [ ] Team is notified of deployment

**Approved By**: _______________

**Date**: _______________
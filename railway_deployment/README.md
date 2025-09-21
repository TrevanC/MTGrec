# Railway Deployment Files

This directory contains all the necessary files and configurations for deploying the MTG Recommender application on Railway.

## Files Overview

### Dockerfiles
- `Dockerfile.backend` - Production-ready Dockerfile for the FastAPI backend
- `Dockerfile.frontend` - Production-ready Dockerfile for the Next.js frontend

### Configuration Files
- `railway.json` - Railway-specific deployment configuration
- `next.config.js` - Next.js configuration optimized for Railway deployment
- `env.backend.example` - Example environment variables for backend service
- `env.frontend.example` - Example environment variables for frontend service

### Documentation
- `RAILWAY_DEPLOYMENT.md` - Comprehensive deployment guide with step-by-step instructions

## Quick Start

1. **Read the deployment guide**: Start with `RAILWAY_DEPLOYMENT.md` for detailed instructions
2. **Set up backend**: Use `Dockerfile.backend` and `env.backend.example`
3. **Set up frontend**: Use `Dockerfile.frontend` and `env.frontend.example`
4. **Configure environment**: Update environment variables in Railway dashboard

## Key Differences from Local Development

- **No Docker Compose**: Railway doesn't support Docker Compose, so services are deployed separately
- **Production builds**: Dockerfiles are optimized for production (no hot reload, smaller images)
- **Managed PostgreSQL**: Railway provides managed PostgreSQL instead of containerized database
- **Environment variables**: All configuration is done through Railway's environment variable system
- **Automatic HTTPS**: Railway provides HTTPS URLs automatically

## Support

For issues or questions:
1. Check the troubleshooting section in `RAILWAY_DEPLOYMENT.md`
2. Review Railway's official documentation
3. Check Railway dashboard logs for detailed error messages

# Railway Deployment Guide for MTG Recommender

This guide explains how to deploy the MTG Recommender application on Railway platform.

## Overview

Railway doesn't support Docker Compose, so we need to deploy each service separately:
- **Backend Service**: FastAPI application with PostgreSQL database
- **Frontend Service**: Next.js application

## Prerequisites

1. Railway account (sign up at [railway.app](https://railway.app))
2. Railway CLI installed (`npm install -g @railway/cli`)
3. Git repository with your code

## Deployment Steps

### Step 1: Deploy Backend Service

1. **Create a new Railway project**:
   ```bash
   railway login
   railway init
   ```

2. **Add PostgreSQL database**:
   - In Railway dashboard, go to your project
   - Click "New" → "Database" → "PostgreSQL"
   - Railway will automatically provide `DATABASE_URL` environment variable

3. **Configure Backend Service**:
   - Copy `Dockerfile.backend` to your project root as `Dockerfile`
   - Or create a new service and specify the Dockerfile path

4. **Set Environment Variables**:
   ```
   DEBUG=false
   DATABASE_URL=<provided by Railway PostgreSQL>
   BACKEND_CORS_ORIGINS=https://your-frontend-domain.railway.app
   ```

5. **Deploy Backend**:
   ```bash
   railway up
   ```

### Step 2: Deploy Frontend Service

1. **Create a new Railway project** (separate from backend):
   ```bash
   railway init
   ```

2. **Configure Frontend Service**:
   - Copy `Dockerfile.frontend` to your project root as `Dockerfile`
   - Update `next.config.js` to enable standalone output:
     ```javascript
     /** @type {import('next').NextConfig} */
     const nextConfig = {
       output: 'standalone',
     }
     
     module.exports = nextConfig
     ```

3. **Set Environment Variables**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-domain.railway.app/api/v1
   API_URL=https://your-backend-domain.railway.app
   ```

4. **Deploy Frontend**:
   ```bash
   railway up
   ```

### Step 3: Database Migration

After backend deployment, run database migrations:

1. **Connect to your Railway backend service**:
   ```bash
   railway shell
   ```

2. **Run Alembic migrations**:
   ```bash
   alembic upgrade head
   ```

## Environment Variables Reference

### Backend Service
| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |
| `DEBUG` | Enable debug mode | `false` (production) |
| `BACKEND_CORS_ORIGINS` | Allowed CORS origins | `https://your-frontend.railway.app` |
| `DATASET_PATH` | Path to dataset file | `/app/data/processed/compact_dataset.json.gz` |
| `SIMILARITY_MODEL_PATH` | Path to similarity model | `/app/data/processed/similarity_model.pkl` |

### Frontend Service
| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Public API URL for client-side | `https://your-backend.railway.app/api/v1` |
| `API_URL` | Internal API URL for server-side | `https://your-backend.railway.app` |

## Important Notes

### Data Files
- The ML model files (`compact_dataset.json.gz`, `similarity_model.pkl`) are included in the Docker image
- For large files (>100MB), consider using Railway volumes or external storage

### CORS Configuration
- Update `BACKEND_CORS_ORIGINS` to include your frontend domain
- Railway provides HTTPS URLs automatically

### Database
- Railway PostgreSQL is managed and automatically backed up
- Connection pooling is handled automatically
- No need to manage database containers

### Monitoring
- Railway provides built-in monitoring and logs
- Check Railway dashboard for service health and performance metrics

## Troubleshooting

### Common Issues

1. **Build Failures**:
   - Check Dockerfile syntax
   - Ensure all required files are copied
   - Verify Node.js/Python versions

2. **Database Connection Issues**:
   - Verify `DATABASE_URL` is set correctly
   - Check if migrations have run successfully
   - Ensure PostgreSQL service is running

3. **CORS Errors**:
   - Update `BACKEND_CORS_ORIGINS` with correct frontend URL
   - Check if frontend is making requests to correct backend URL

4. **Missing Data Files**:
   - Verify data files are copied in Dockerfile
   - Check file paths in environment variables

### Logs and Debugging

- Use `railway logs` to view service logs
- Check Railway dashboard for detailed error messages
- Enable debug mode temporarily if needed (set `DEBUG=true`)

## Cost Optimization

- Railway charges based on resource usage
- Consider using smaller instance sizes for development
- Monitor usage in Railway dashboard
- Use Railway's free tier for testing

## Security Considerations

- Never commit sensitive data to repository
- Use Railway's environment variables for secrets
- Enable HTTPS (automatic with Railway)
- Regularly update dependencies
- Use non-root users in Docker containers (implemented in Dockerfiles)

## Next Steps

After successful deployment:
1. Set up custom domains (optional)
2. Configure CI/CD for automatic deployments
3. Set up monitoring and alerting
4. Implement backup strategies for data
5. Consider scaling options based on usage

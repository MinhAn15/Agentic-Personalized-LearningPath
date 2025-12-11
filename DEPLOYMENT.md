# Deployment Guide

## 🚀 Frontend Deployment (Vercel)

### Prerequisites

- Git repository on GitHub/GitLab/Bitbucket
- Vercel account (free tier available)

### Steps

1. **Push to Git**

```bash
git add .
git commit -m "🚀 Ready for production"
git push origin main
```

2. **Connect to Vercel**

- Go to [vercel.com](https://vercel.com)
- Click "New Project"
- Import your repository
- Select the `frontend` folder as root directory

3. **Configure Environment Variables**

```
NEXT_PUBLIC_API_URL=https://your-backend-api.com
NEXT_PUBLIC_WS_URL=wss://your-backend-api.com
```

4. **Deploy Settings**

- Framework Preset: Next.js
- Build Command: `npm run build`
- Output Directory: `.next`

5. **Click Deploy!** ✅

---

## 🐳 Backend Deployment (Docker)

### Build Docker Image

```bash
# From project root
docker build -f Dockerfile.backend -t pathai-backend:latest .
```

### Run Locally

```bash
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e NEO4J_URI=bolt://neo4j:7687 \
  -e GOOGLE_API_KEY=your-key \
  pathai-backend:latest
```

### Push to Registry

```bash
# AWS ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.us-east-1.amazonaws.com
docker tag pathai-backend:latest 123456789.dkr.ecr.us-east-1.amazonaws.com/pathai-backend:latest
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/pathai-backend:latest

# Docker Hub
docker tag pathai-backend:latest username/pathai-backend:latest
docker push username/pathai-backend:latest
```

### Deploy Options

#### Option A: AWS ECS/Fargate

```bash
# Create task definition and service via AWS Console or CLI
```

#### Option B: Google Cloud Run

```bash
gcloud run deploy pathai-backend \
  --image gcr.io/your-project/pathai-backend:latest \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Option C: Railway/Render

- Connect Git repo
- Set environment variables
- Auto-deploy on push

---

## 🗄️ Database Setup

### PostgreSQL (Production)

```bash
# Create database
createdb pathai_production

# Run migrations (if using Alembic)
alembic upgrade head
```

### Neo4j (Managed)

- Use Neo4j Aura (managed service)
- Or deploy Neo4j Enterprise on Kubernetes

### Redis (Caching)

- Use ElastiCache (AWS) or Upstash
- Or run Redis container alongside

---

## 🔧 Environment Variables

### Frontend (.env.production)

```env
NEXT_PUBLIC_API_URL=https://api.yourapp.com
NEXT_PUBLIC_WS_URL=wss://api.yourapp.com
```

### Backend (.env)

```env
# API Settings
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Neo4j
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# Redis
REDIS_URL=redis://redis:6379

# LLM
GOOGLE_API_KEY=your_google_api_key
LLM_MODEL=gemini-1.5-flash

# Security
SECRET_KEY=your-secret-key-min-32-chars
ALLOWED_ORIGINS=https://yourapp.com,https://www.yourapp.com
```

---

## ✅ Post-Deployment Checklist

### Health Checks

```bash
# Backend health
curl https://api.yourapp.com/health

# Frontend health
curl https://yourapp.com/
```

### Test Workflows

- [ ] Sign up new user
- [ ] Sign in existing user
- [ ] View dashboard
- [ ] Start tutor session
- [ ] Submit answer and get feedback
- [ ] View progress page
- [ ] Upload content

### Monitoring Setup

- [ ] Sentry for error tracking
- [ ] CloudWatch/Datadog for metrics
- [ ] Uptime monitoring (Pingdom, UptimeRobot)
- [ ] Log aggregation (Papertrail, Logtail)

### Performance

- [ ] Check Lighthouse score
- [ ] Verify bundle size < 200KB
- [ ] Test mobile responsiveness
- [ ] Check TTFB < 200ms

---

## 🎉 Launch Checklist

- [ ] Domain configured with SSL
- [ ] Environment variables set
- [ ] Database migrated
- [ ] Health checks passing
- [ ] Monitoring active
- [ ] Backups configured
- [ ] Documentation updated
- [ ] Team notified
- [ ] GO LIVE! 🚀

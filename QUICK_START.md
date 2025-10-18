# Quick Start Guide

Get the URL Shortener running in 5 minutes!

## Prerequisites
- Docker & Docker Compose installed
- Node.js 18+ installed

## Step 1: Environment Setup (2 minutes)

### Backend Environment
```bash
# Copy example environment files
cp .envs/.local/.django.example .envs/.local/.django
cp .envs/.local/.postgres.example .envs/.local/.postgres

# Edit .envs/.local/.django and set:
# - DJANGO_SECRET_KEY (generate a new one)
# - USE_S3=False (for local development)
```

## Step 2: Start Backend (2 minutes)

```bash
# Build and start all services
docker-compose -f local.yml up --build -d

# Run database migrations
docker-compose -f local.yml run --rm django python manage.py migrate

# Create a superuser (optional, for admin access)
docker-compose -f local.yml run --rm django python manage.py createsuperuser
```

Backend will be available at: http://localhost:8000

## Step 3: Start Frontend (1 minute)

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Create environment file
echo "VITE_API_URL=http://localhost:8000" > .env

# Start development server
npm run dev
```

Frontend will be available at: http://localhost:5173

## Step 4: Test It Out!

1. **Register**: Go to http://localhost:5173/register
   - Create a new account
   - An organization will be auto-created for you

2. **Create a Namespace**:
   - Go to Organizations → Click your organization
   - Click "Create Namespace"
   - Enter name: `test` (must be globally unique)

3. **Create a Short URL**:
   - Go to URLs → Click "Create Short URL"
   - Select namespace: `test`
   - Original URL: `https://google.com`
   - Custom code: `google` (or leave empty for auto-generated)
   - Click Create

4. **Test the Redirect**:
   - Open: http://localhost:8000/test/google/
   - You should be redirected to Google!

## Useful Commands

### Backend

```bash
# View logs
docker-compose -f local.yml logs -f

# View Django logs only
docker-compose -f local.yml logs -f django

# View Celery logs
docker-compose -f local.yml logs -f celeryworker

# Access Django shell
docker-compose -f local.yml run --rm django python manage.py shell

# Stop all services
docker-compose -f local.yml down

# Stop and remove volumes (fresh start)
docker-compose -f local.yml down -v
```

### Frontend

```bash
# Install new dependencies
npm install package-name

# Build for production
npm run build

# Preview production build
npm run preview
```

## API Access

### Get JWT Token
```bash
curl -X POST http://localhost:8000/rest-auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'
```

### Create Short URL via API
```bash
curl -X POST http://localhost:8000/api/short-urls/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace_id": 1,
    "original_url": "https://example.com",
    "short_code": "example"
  }'
```

## Bulk Upload Example

1. Create `urls.xlsx` with:
   | original_url | custom_short_code |
   |-------------|-------------------|
   | https://google.com | google |
   | https://github.com | gh |
   | https://stackoverflow.com |  |

2. Go to Bulk Upload page in UI
3. Select your namespace
4. Upload the file
5. Wait for processing
6. Download result file

## Admin Interface

Access Django admin at: http://localhost:8000/admin/
- View all models
- Manage users, organizations, namespaces, URLs
- Monitor bulk upload tasks

## API Documentation

Swagger UI: http://localhost:8000/api/docs/
- Interactive API documentation
- Test endpoints directly
- View request/response schemas

## Monitoring

Celery Flower: http://localhost:5555/
- Monitor Celery tasks
- View task history
- Check worker status

## Troubleshooting

**Port already in use:**
```bash
# Change ports in docker-compose local.yml or vite.config.js
```

**Database connection error:**
```bash
# Ensure PostgreSQL container is running
docker-compose -f local.yml ps postgres
```

**CORS error in frontend:**
```bash
# Check that Django is running on port 8000
# Verify CORS settings in config/settings/local.py
```

**Celery task not processing:**
```bash
# Restart celery worker
docker-compose -f local.yml restart celeryworker
```

## Next Steps

- Read [URL_SHORTENER_README.md](URL_SHORTENER_README.md) for detailed documentation
- Read [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for technical details
- Check [bulk_upload_template.md](bulk_upload_template.md) for Excel format

## Need Help?

1. Check container logs: `docker-compose -f local.yml logs`
2. Ensure all services are running: `docker-compose -f local.yml ps`
3. Review Django settings: `config/settings/base.py` and `config/settings/local.py`
4. Check frontend console for errors

---

Happy URL shortening! 🚀


# URL Shortener Platform

A comprehensive namespaced URL shortening platform with Django REST API backend and React frontend, featuring organization management, role-based access control, and bulk processing.

## Features

### Core Features
- **Organizations**: Auto-created on user signup, users can create multiple organizations
- **Namespaces**: Globally unique namespaces per organization
- **Role-Based Access Control**:
  - **Admin**: Full control (create namespaces, invite users, manage URLs)
  - **Editor**: Create, edit, and delete short URLs
  - **Viewer**: View-only access to short URLs
- **Custom Short Codes**: User-provided or auto-generated short codes
- **Bulk Upload**: Upload Excel files with multiple URLs, async processing with Celery
- **S3 Storage**: File storage for Excel files and QR codes

### Additional Features
- **QR Code Generation**: Generate QR codes for short URLs
- **Private URLs**: JWT-authenticated URL access
- **URL Analytics**: Click count and timestamps
- **Tags**: Categorize URLs with tags
- **Expiring URLs**: Auto-expire URLs after a specified date
- **Email Invitations**: Invite members to organizations

## Tech Stack

### Backend
- Django 4.2.3
- Django REST Framework
- PostgreSQL
- Celery + Redis (async tasks)
- django-storages + boto3 (S3 integration)
- djangorestframework-simplejwt (JWT auth)
- openpyxl (Excel processing)
- qrcode (QR code generation)

### Frontend
- React 18 with Vite
- React Router (routing)
- TanStack Query (data fetching)
- Zustand (state management)
- Tailwind CSS (styling)
- Axios (HTTP client)

## Project Structure

```
hirethon-django-template/
├── config/                 # Django configuration
├── hirethon_template/
│   ├── users/             # User management
│   └── url_shortener/     # URL shortener app
│       ├── models.py      # Database models
│       ├── signals.py     # Signal handlers
│       ├── tasks.py       # Celery tasks
│       ├── admin.py       # Django admin
│       └── api/
│           ├── serializers.py
│           ├── views.py
│           └── permissions.py
├── frontend/              # React application
│   ├── src/
│   │   ├── api/          # API client functions
│   │   ├── components/   # Reusable components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom React hooks
│   │   ├── store/        # Zustand stores
│   │   └── utils/        # Utility functions
│   └── package.json
├── requirements/          # Python dependencies
└── local.yml             # Docker Compose config
```

## Setup Instructions

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for local development)

### Backend Setup (Docker)

1. **Create environment files**:

Create `.envs/.local/.django`:
```bash
USE_DOCKER=yes
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
CELERY_BROKER_URL=redis://redis:6379/0

# AWS S3 (optional for local, required for production)
USE_S3=False
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=url-shortener-dev
AWS_S3_REGION_NAME=us-east-1
```

Create `.envs/.local/.postgres`:
```bash
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=hirethon_template
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

2. **Build and start services**:
```bash
docker-compose -f local.yml build
docker-compose -f local.yml up
```

3. **Run migrations**:
```bash
docker-compose -f local.yml run --rm django python manage.py migrate
```

4. **Create superuser**:
```bash
docker-compose -f local.yml run --rm django python manage.py createsuperuser
```

The Django API will be available at http://localhost:8000

### Frontend Setup

1. **Install dependencies**:
```bash
cd frontend
npm install
```

2. **Create `.env` file** in `frontend/` directory:
```bash
VITE_API_URL=http://localhost:8000
```

3. **Start development server**:
```bash
npm run dev
```

The React app will be available at http://localhost:5173

## API Endpoints

### Authentication
- `POST /rest-auth/registration/` - User registration
- `POST /rest-auth/login/` - User login
- `POST /rest-auth/logout/` - User logout
- `GET /rest-auth/user/` - Get current user
- `POST /rest-auth/token/refresh/` - Refresh JWT token

### Organizations
- `GET /api/organizations/` - List user's organizations
- `POST /api/organizations/` - Create organization
- `GET /api/organizations/{id}/` - Organization detail
- `PATCH /api/organizations/{id}/` - Update organization
- `DELETE /api/organizations/{id}/` - Delete organization
- `POST /api/organizations/{id}/invite/` - Invite member
- `GET /api/organizations/{id}/members/` - List members

### Namespaces
- `GET /api/namespaces/` - List namespaces
- `POST /api/namespaces/` - Create namespace (admin only)
- `GET /api/namespaces/{id}/` - Namespace detail
- `DELETE /api/namespaces/{id}/` - Delete namespace (admin only)

### Short URLs
- `GET /api/short-urls/` - List short URLs
- `POST /api/short-urls/` - Create short URL (admin/editor)
- `GET /api/short-urls/{id}/` - URL detail
- `PATCH /api/short-urls/{id}/` - Update URL (admin/editor)
- `DELETE /api/short-urls/{id}/` - Delete URL (admin/editor)
- `POST /api/short-urls/{id}/generate_qr/` - Generate QR code

### Bulk Upload
- `GET /api/bulk-upload/` - List bulk upload tasks
- `POST /api/bulk-upload/` - Create bulk upload task
- `GET /api/bulk-upload/{id}/` - Task status
- `GET /api/bulk-upload/{id}/download/` - Download result

### URL Redirection
- `GET /{namespace}/{short_code}/` - Redirect to original URL

## Usage Examples

### Creating a Short URL

**Via API:**
```bash
curl -X POST http://localhost:8000/api/short-urls/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "namespace_id": 1,
    "original_url": "https://example.com/very/long/url",
    "short_code": "my-code",
    "tags": "marketing,campaign"
  }'
```

**Via Frontend:**
1. Login to the application
2. Navigate to "URLs" section
3. Click "Create Short URL"
4. Fill in the form and submit

### Bulk Upload

1. Prepare an Excel file with columns:
   - `original_url` (required)
   - `custom_short_code` (optional)

2. Navigate to "Bulk Upload" page
3. Select organization and namespace
4. Upload the Excel file
5. Wait for processing (polls every 2 seconds)
6. Download result file with shortened URLs

### URL Redirection

Once a short URL is created, it can be accessed at:
```
http://your-domain.com/{namespace}/{short_code}/
```

Example:
```
http://localhost:8000/my-namespace/my-code/
```

## Development

### Running Tests

Backend:
```bash
docker-compose -f local.yml run --rm django pytest
```

### API Documentation

Swagger UI is available at:
- http://localhost:8000/api/docs/

OpenAPI schema:
- http://localhost:8000/api/schema/

### Admin Interface

Django admin is available at:
- http://localhost:8000/admin/

## Production Deployment

1. Update `.envs/.production/` files with production credentials
2. Set `USE_S3=True` and configure AWS credentials
3. Build production images:
```bash
docker-compose -f production.yml build
```

4. Run migrations:
```bash
docker-compose -f production.yml run --rm django python manage.py migrate
```

5. Collect static files:
```bash
docker-compose -f production.yml run --rm django python manage.py collectstatic --noinput
```

6. Start services:
```bash
docker-compose -f production.yml up -d
```

## Environment Variables

### Django Settings

- `DJANGO_DEBUG` - Debug mode (default: False)
- `DJANGO_SECRET_KEY` - Django secret key
- `DJANGO_ALLOWED_HOSTS` - Allowed hosts (comma-separated)
- `DATABASE_URL` - PostgreSQL connection URL
- `CELERY_BROKER_URL` - Redis URL for Celery
- `USE_S3` - Enable S3 storage (default: False)
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_STORAGE_BUCKET_NAME` - S3 bucket name
- `AWS_S3_REGION_NAME` - S3 region (default: us-east-1)

### Frontend Settings

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Troubleshooting

### Backend Issues

**Migrations not applying:**
```bash
docker-compose -f local.yml run --rm django python manage.py makemigrations
docker-compose -f local.yml run --rm django python manage.py migrate
```

**Celery not processing tasks:**
```bash
# Check celery logs
docker-compose -f local.yml logs celeryworker

# Restart celery
docker-compose -f local.yml restart celeryworker
```

### Frontend Issues

**API calls failing:**
- Check that Django is running on port 8000
- Verify CORS settings in `config/settings/local.py`
- Check browser console for errors

**Build errors:**
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## License

This project is licensed under the MIT License.

## Contributors

Built with the Hirethon Django Template.


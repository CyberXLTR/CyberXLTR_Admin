# CyberXLTR Admin Setup Guide

This guide will help you set up the CyberXLTR Admin platform as a separate repository from the main CyberXLTR application.

## What Has Been Created

A complete admin platform with:

### Backend (FastAPI + PostgreSQL)
- `/backend/src/core/` - Core configuration and database
- `/backend/src/models/` - SQLAlchemy models (User, Organization, UserOrganization, Notification)
- `/backend/src/api/` - API routers
  - `auth.py` - Authentication utilities
  - `dependencies.py` - Admin verification
  - `routers/admin_auth.py` - Admin login
  - `routers/organizations.py` - Organization CRUD
  - `routers/users.py` - User CRUD
  - `routers/notifications.py` - Notification CRUD
- `/backend/migrations/` - Alembic database migrations
- `/backend/run.py` - Application entry point

### Frontend (Next.js + TypeScript)
- `/frontend/src/app/` - Next.js app directory
  - `login/` - Admin login page
  - `dashboard/` - Dashboard layout and pages
    - `organizations/` - Organization management
    - `users/` - User management
    - `notifications/` - Notification management
    - `settings/` - System settings
- `/frontend/src/components/` - Reusable components
- `/frontend/src/lib/` - API client
- `/frontend/src/store/` - Zustand state management

### Deployment
- `docker-compose.yml` - Multi-container Docker setup
- Backend and Frontend Dockerfiles
- PostgreSQL database configuration

## Quick Start

### Option 1: Docker Compose (Recommended)

1. Navigate to the admin directory:
```bash
cd CyberXLTR_Admin
```

2. Create environment files:
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your configuration

# Frontend
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local
```

3. Start all services:
```bash
docker-compose up -d
```

4. Run database migrations:
```bash
docker-compose exec backend alembic upgrade head
```

5. Create admin user:
```bash
docker-compose exec backend python create_admin.py
```

6. Access the platform:
- Frontend: http://localhost:3001
- Backend: http://localhost:8001
- API Docs: http://localhost:8001/docs

Default admin credentials:
- Email: admin@cyberxltr.com
- Password: Cyberxltr#01

**IMPORTANT: Change the password immediately after first login!**

### Option 2: Manual Setup

#### Backend Setup

1. Set up Python environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Set up PostgreSQL database:
```bash
# Create database
createdb cyberxltr_admin

# Or using psql:
psql -U postgres
CREATE DATABASE cyberxltr_admin;
\q
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Run migrations:
```bash
alembic upgrade head
```

5. Create admin user:
```bash
python create_admin.py
```

6. Start backend:
```bash
python run.py
```

Backend will run on http://localhost:8001

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment:
```bash
cp .env.example .env.local
# Edit .env.local
```

3. Start frontend:
```bash
npm run dev
```

Frontend will run on http://localhost:3001

## Database Schema

The following tables are created:

- `users` - System users
- `organizations` - Customer organizations
- `user_organizations` - User-Organization relationships
- `notifications` - System notifications

## Configuration

### Backend Environment Variables

```bash
# Database
DATABASE_URL=postgresql://admin:password@localhost:5432/cyberxltr_admin

# Security
JWT_SECRET_KEY=your-secret-key-min-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Server
HOST=0.0.0.0
PORT=8001
ENVIRONMENT=development
DEBUG=True
```

### Frontend Environment Variables

```bash
NEXT_PUBLIC_API_URL=http://localhost:8001
```

## AWS RDS Deployment

### 1. Create RDS Instance

1. Go to AWS RDS Console
2. Create PostgreSQL 15 instance
3. Configure security groups to allow access
4. Note the endpoint, username, and password

### 2. Update Backend Configuration

```bash
# In backend/.env
DATABASE_URL=postgresql://username:password@rds-endpoint:5432/cyberxltr_admin
ENVIRONMENT=production
DEBUG=False
JWT_SECRET_KEY=generate-strong-32-char-key
```

### 3. Run Migrations on RDS

```bash
cd backend
alembic upgrade head
python create_admin.py
```

### 4. Deploy to Cloud

Deploy backend and frontend to your preferred hosting:
- AWS ECS/EKS
- AWS Elastic Beanstalk
- DigitalOcean App Platform
- Heroku

## Admin User Management

The admin email list is configured in:
- `backend/src/api/auth.py` - Line 21: `ADMIN_EMAILS = ["admin@cyberxltr.com"]`

To add more admin users:
1. Edit the ADMIN_EMAILS list
2. Create users via the admin panel
3. Only emails in this list can access admin functions

## Security Notes

1. Change default admin password immediately
2. Use strong JWT_SECRET_KEY (min 32 characters)
3. Enable HTTPS in production
4. Configure CORS for production domains
5. Use environment variables for all secrets
6. Enable PostgreSQL SSL in production

## Troubleshooting

### Backend won't start
- Check database connection in .env
- Ensure PostgreSQL is running
- Verify migrations are up to date

### Frontend can't connect to backend
- Check NEXT_PUBLIC_API_URL in .env.local
- Ensure backend is running
- Check CORS configuration

### Database connection errors
- Verify DATABASE_URL format
- Check PostgreSQL is accessible
- Ensure database exists

## Next Steps

1. Customize admin email list
2. Configure production environment variables
3. Set up AWS RDS
4. Deploy backend and frontend
5. Configure domain names
6. Set up SSL certificates
7. Configure backup strategy
8. Monitor logs and performance

## Support

For issues or questions, refer to:
- Backend API docs: http://localhost:8001/docs
- Application logs: `docker-compose logs -f`


# CyberXLTR Admin - Migration Summary

This document summarizes the migration of the admin section from CyberXLTR to CyberXLTR_Admin as a separate repository.

## Key Changes

### 1. Database Technology
**Before (CyberXLTR):** Supabase
**After (CyberXLTR_Admin):** PostgreSQL with SQLAlchemy + asyncpg

**Why:** To prepare for AWS RDS deployment and have full control over the database.

### 2. Repository Structure
The admin system is now completely separate:
- **CyberXLTR:** Main application for customers/sales
- **CyberXLTR_Admin:** Administrative platform for system management

### 3. Database Architecture

#### New PostgreSQL Schema
```sql
-- Users table
users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE,
  encrypted_password VARCHAR(255),
  first_name, last_name, full_name,
  global_role VARCHAR(50),
  is_active BOOLEAN,
  email_verified BOOLEAN,
  created_at, updated_at TIMESTAMP
)

-- Organizations table
organizations (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  url VARCHAR(255) UNIQUE,
  subscription_tier VARCHAR(50),
  max_storage_gb INTEGER,
  features JSONB,
  settings JSONB,
  security_settings JSONB,
  is_active BOOLEAN,
  created_at, updated_at TIMESTAMP
)

-- User-Organization junction
user_organizations (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  organization_id UUID REFERENCES organizations(id),
  role VARCHAR(50),
  is_active BOOLEAN,
  is_primary BOOLEAN
)

-- Notifications table
notifications (
  id UUID PRIMARY KEY,
  title VARCHAR(255),
  message TEXT,
  type VARCHAR(50),
  target VARCHAR(50),
  target_spec JSONB,
  priority INTEGER,
  is_active BOOLEAN,
  created_by UUID REFERENCES users(id),
  expires_at TIMESTAMP
)
```

### 4. Backend Changes

#### From Supabase Client to SQLAlchemy
**Before:**
```python
from ....core.supabase_client import supabase_client
result = supabase_client.client.table("users").select("*").execute()
```

**After:**
```python
from sqlalchemy import select
from ...models import User

async with db_client.get_session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()
```

#### Authentication Changes
**Before:** Supabase Auth with JWT
**After:** Custom JWT authentication with bcrypt password hashing

**Admin Verification:**
- Admin emails are whitelisted in `backend/src/api/auth.py`
- Only whitelisted emails can access admin endpoints
- JWT tokens have `scope: "admin"` for admin users

### 5. Frontend Changes

#### Removed from Admin
- Supabase client dependency
- Direct database access from frontend

#### Added to Admin
- Axios API client with JWT token management
- Zustand for state management
- Automatic token refresh and error handling

### 6. Deployment Changes

#### Database
**Before:** Supabase hosted database
**After:** PostgreSQL (local development) → AWS RDS (production)

#### Backend
**Before:** Shared with main app
**After:** Separate FastAPI instance on port 8001

#### Frontend
**Before:** Part of main Next.js app
**After:** Separate Next.js instance on port 3001

## File Mapping

### Backend Files Migrated

| Original (CyberXLTR) | New (CyberXLTR_Admin) | Changes |
|---------------------|----------------------|---------|
| `backend/src/app/api/v1/routers/admin.py` | `backend/src/api/routers/organizations.py`, `users.py`, `notifications.py` | Split into separate routers, converted to SQLAlchemy |
| `backend/src/app/core/supabase_client.py` | `backend/src/core/database.py` | Replaced with PostgreSQL client |
| `backend/src/app/core/config.py` | `backend/src/core/config.py` | Simplified, removed Supabase config |
| N/A | `backend/src/models/*.py` | New SQLAlchemy models |
| N/A | `backend/migrations/*` | New Alembic migrations |

### Frontend Files Migrated

| Original (CyberXLTR) | New (CyberXLTR_Admin) | Changes |
|---------------------|----------------------|---------|
| `frontend/src/app/admin/dashboard/` | `frontend/src/app/dashboard/` | Renamed, updated API calls |
| `frontend/src/components/AdminSidebar.tsx` | `frontend/src/components/Sidebar.tsx` | Simplified navigation |
| `frontend/src/app/admin/login/page.tsx` | `frontend/src/app/login/page.tsx` | Updated auth flow |

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Admin login

### Organizations
- `GET /api/v1/organizations/` - List all organizations
- `GET /api/v1/organizations/{id}` - Get organization details
- `POST /api/v1/organizations/` - Create organization
- `PUT /api/v1/organizations/{id}` - Update organization
- `DELETE /api/v1/organizations/{id}` - Deactivate organization
- `POST /api/v1/organizations/{id}/reactivate` - Reactivate organization

### Users
- `GET /api/v1/users/` - List all users
- `GET /api/v1/users/{id}` - Get user details
- `POST /api/v1/users/` - Create user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Deactivate user
- `POST /api/v1/users/{id}/reactivate` - Reactivate user

### Notifications
- `GET /api/v1/notifications/` - List all notifications
- `GET /api/v1/notifications/{id}` - Get notification details
- `POST /api/v1/notifications/` - Create notification
- `PUT /api/v1/notifications/{id}` - Update notification
- `DELETE /api/v1/notifications/{id}` - Deactivate notification
- `GET /api/v1/notifications/stats/overview` - Get notification stats

## What Was NOT Changed in CyberXLTR

As requested, the original CyberXLTR repository remains unchanged:
- All admin files remain in place
- Supabase configuration unchanged
- No deletions or modifications

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│         CyberXLTR_Admin                 │
│  (Separate Deployment)                  │
├─────────────────────────────────────────┤
│                                         │
│  Frontend (Next.js)                     │
│  Port: 3001                             │
│  Domain: admin.cyberxltr.com            │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  Backend (FastAPI)                      │
│  Port: 8001                             │
│  Domain: admin-api.cyberxltr.com        │
│                                         │
├─────────────────────────────────────────┤
│                                         │
│  PostgreSQL (AWS RDS)                   │
│  Database: cyberxltr_admin              │
│                                         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         CyberXLTR                       │
│  (Main Application)                     │
├─────────────────────────────────────────┤
│  Frontend + Backend + Supabase          │
│  Domain: app.cyberxltr.com              │
└─────────────────────────────────────────┘
```

## Migration Checklist

- [x] Backend structure created
- [x] PostgreSQL models defined
- [x] Database migrations created
- [x] Admin API routers implemented
- [x] Authentication system created
- [x] Frontend structure created
- [x] Dashboard pages created
- [x] Docker configuration created
- [x] Documentation created
- [ ] Deploy to AWS RDS
- [ ] Deploy backend to cloud
- [ ] Deploy frontend to cloud
- [ ] Configure domain names
- [ ] Set up SSL certificates
- [ ] Test admin functionality
- [ ] Update admin email list
- [ ] Change default passwords

## Next Steps

1. **Set up AWS RDS:**
   - Create PostgreSQL 15 instance
   - Configure security groups
   - Run migrations

2. **Deploy Services:**
   - Deploy backend (ECS/Elastic Beanstalk)
   - Deploy frontend (Vercel/Netlify/S3+CloudFront)

3. **Configure Production:**
   - Update environment variables
   - Set up domain names
   - Configure SSL
   - Update CORS settings

4. **Security:**
   - Change default admin password
   - Update JWT secret key
   - Configure admin email list
   - Enable database SSL

5. **Testing:**
   - Test all CRUD operations
   - Verify authentication
   - Check authorization
   - Test deployment

## Support

For questions or issues:
- Review SETUP.md for setup instructions
- Check README.md for general information
- Review backend API docs at /docs endpoint


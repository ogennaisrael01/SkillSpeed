# Skill Speed Backend API

## Overview

Skill Speed is a Django REST Framework backend API designed to expose children (ages 5–15) to technology, craft, and vocational skills. The platform provides age-appropriate skill paths, structured lesson content, enrollment-controlled access, progress tracking, and AI-powered recommendations. Guardians register and onboard children, who then enroll in skill paths filtered by age eligibility and complete lessons with tracked progress.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Project Structure
The Django project lives inside the `src/` directory. The main project configuration is in `src/core/` and all apps are under `src/apps/`. Tests use pytest with fixtures and factories organized in `src/tests_config/`.

```
src/
├── core/                    # Django project config (settings, urls, celery, wsgi/asgi)
│   ├── settings/
│   │   ├── base.py          # Shared settings
│   │   ├── development.py   # Dev settings (debug toolbar, silk, local redis)
│   │   └── production.py    # Production settings (dj_database_url, env-based)
│   ├── celery.py            # Celery app configuration
│   ├── urls.py              # Root URL configuration
│   └── service.py           # Health check and test endpoints
├── apps/
│   ├── users/               # Authentication, registration, OTP, password reset
│   │   ├── profiles/        # Guardian, Instructor, ChildProfile, Certificates, Interests
│   │   ├── services/        # Email service (SendGrid), Celery tasks, OTP helpers
│   │   ├── auth_models.py   # Custom user model (CustomUser with AbstractBaseUser)
│   │   └── auth.py          # JWT token customization (SimpleJWT)
│   ├── skills/              # Skill categories, skills, enrollments
│   │   └── payments/        # Chapa payment integration for paid skills
│   └── lesson/              # Lesson content, progress tracking, projects, submissions
│       └── recommendation/  # Age-based and AI-based skill recommendations
├── tests_config/            # Test configuration
│   ├── factories/           # Factory Boy factories for test data
│   ├── fixtures/            # Pytest fixtures (auth, profiles, users, utils)
│   └── settings.py          # Test-specific Django settings
└── manage.py
```

### Custom User Model
- Uses `AbstractBaseUser` + `PermissionsMixin` with UUID primary keys
- `AUTH_USER_MODEL = "users.CustomUser"`
- User roles: INSTRUCTOR, GUARDIAN (set during onboarding)
- Active profile switching between CHILD and GUARDIAN accounts
- Account statuses: ACTIVE, SUSPENDED, DEACTIVATED

### Authentication & Authorization
- **JWT authentication** via `djangorestframework-simplejwt` with token blacklisting for logout
- **Custom token serializer** that validates email, checks account verification, and embeds user data
- **OTP-based email verification** after registration (codes are hashed and stored, auto-expired via Celery beat)
- **Password reset** flow with token generation and email delivery
- **Custom permissions**: IsGuardian, IsInstructor, IsAdminOrInstructor, ChildRole, IsOwner, ChildProfileOwner

### Core Domain Models
1. **Users**: CustomUser → Guardian/Instructor profiles, ChildProfile (linked to guardian), ChildInterest, Certificates
2. **Skills**: SkillCategory (TECH/VOCATIONAL/CRAFT) → Skills (with age ranges, difficulty, pricing) → Enrollment (links child to skill)
3. **Lessons**: LessonContent (VIDEO/FILE/TEXT, ordered per skill) → Progress (per child per lesson), Projects, Submissions
4. **Recommendations**: Age-based and AI-based (via Google Gemini) skill recommendations per child
5. **Payments**: Purchase model with Chapa payment gateway integration for paid skills

### API URL Structure
- `api/v1/auth/` — Registration, login, logout, OTP verification, password reset
- `api/v1/profile/` — Onboarding, profile management, child profiles, account switching
- `api/v1/sk/category/` — Skill categories (nested router for skills)
- `api/v1/sk/category/{id}/skills/` — Skills within categories
- `api/v1/sk/child/{id}/skills/{id}/enroll` — Enrollment
- `api/v1/sk/` — Lesson content, projects, submissions (nested under skills)
- `api/v1/sk/child/{id}/recommendations/` — Recommendations
- `api/v1/sk/child/{id}/skill/{id}/purchase/` — Payments

### Background Tasks
- **Celery** with Redis broker handles async email sending, OTP auto-expiration, and password reset code deactivation
- Tasks are defined in `apps/users/services/tasks.py`
- Celery config in `core/celery.py`, auto-discovers tasks from all apps

### Settings Management
- Uses `django-environ` to load from `.env` file
- `DJANGO_SETTINGS_MODULE` env var controls which settings module is active
- Three settings files: `base.py` (shared), `development.py` (debug tools, local Redis), `production.py` (dj_database_url with SSL)

### Database
- **PostgreSQL** in production (via `psycopg2-binary` and `dj_database_url`)
- All models use **UUID primary keys**
- Extensive use of database indexes and unique constraints
- Cursor-based pagination throughout (CursorPagination)

### Testing
- **pytest** with `pytest-django` as the test runner
- **Factory Boy** + **Faker** for test data generation
- Fixtures organized by concern: auth (API clients with JWT), profiles, users, utilities
- Test settings use MD5 password hasher for speed, locmem cache, and locmem email backend
- Celery tasks run eagerly in tests (`CELERY_TASK_ALWAYS_EAGER = True`)
- Configure with: `pytest --ds=tests_config.settings` from the `src/` directory

### API Documentation
- **drf-yasg** provides Swagger UI at `/docs/` and ReDoc at `/redocs/`

## External Dependencies

### Email Service
- **SendGrid** — Transactional emails for OTP verification, password reset. Uses `sendgrid` Python SDK with API key from env (`SENDGRID_API_KEY`, `SENDGRID_SENDER`)

### Payment Gateway
- **Chapa** — Ethiopian payment gateway for paid skill purchases. Config via `CHAPA_SECRET_KEY`, `CHAPA_INIT_URL`, `CHAPA_VERIFY_URL` env vars. Implementation in `apps/skills/payments/`

### AI/ML
- **Google Gemini** — AI-based skill recommendations via `google-genai` SDK. Requires `GEMINI_API_KEY` env var

### Task Queue
- **Redis** — Used as Celery broker/result backend and Django cache backend. Dev uses `redis://localhost:6379`, production uses `REDIS_URL` env var

### Database
- **PostgreSQL** — Primary database. Production uses `DATABASE_URL` env var with SSL required

### Key Python Packages
- `django==5.2.11`, `djangorestframework==3.16.1`
- `djangorestframework-simplejwt` — JWT auth with token blacklisting
- `drf-nested-routers` — Nested REST routes (category → skills)
- `django-filter` — Queryset filtering
- `django-environ` — Environment variable management
- `celery==5.6.2` with `django-redis`
- `drf-yasg` — API documentation
- `gunicorn` — Production WSGI server
- `django-debug-toolbar` and `django-silk` — Dev-only profiling tools
- `factory-boy` and `faker` — Test factories
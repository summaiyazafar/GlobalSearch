@'
# GlobalSearch

Worldwide AI-powered Job Discovery and Application Platform.

## Vision

GlobalSearch helps users discover international job opportunities,
analyze job requirements, evaluate eligibility, generate tailored
resumes and cover letters, and manage authorized job applications.

## Technology Stack

### Frontend
- Next.js
- TypeScript
- Tailwind CSS

### Backend
- Python
- FastAPI
- Pydantic

### Planned Infrastructure
- PostgreSQL / Supabase
- Redis
- Celery
- Docker
- Playwright Python

### AI
- LLM integration
- Job description analysis
- Skill matching
- Eligibility checking
- Resume tailoring

## Current Development Status

- [x] Project structure created
- [x] Backend dependencies installed
- [x] FastAPI application initialized
- [x] Root endpoint implemented
- [x] Health endpoint implemented
- [x] Swagger documentation verified

## Planned Development

1. Git and GitHub setup
2. Frontend initialization
3. Database architecture
4. User authentication
5. User profile and onboarding
6. Job discovery engine
7. Job processing and matching
8. AI resume generation
9. Application management
10. Authorized browser automation
11. Human approval and verification
12. Testing and deployment

## Backend Development

From the project root:

```powershell
python -m uvicorn app.main:app --reload --app-dir backend
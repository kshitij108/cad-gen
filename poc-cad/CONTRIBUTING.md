# Contributing Guide

## Code Structure

### Backend (`backend/`)
- **main.py**: Core FastAPI application with route handlers
- **models.py**: Pydantic data validation models
- **database.py**: SQLAlchemy database configuration
- **utils.py**: Utility functions (hashing, validation, etc.)

### Frontend (`frontend/src/`)
- **app/pages/**: Page components (Login, Register, Dashboard)
- **app/services/**: HTTP services (AuthService, CadService, DashboardService)
- **app/components/**: Reusable components (coming soon)
- **environments/**: Environment-specific configurations

## Development Workflow

### Backend Development
```bash
cd backend
source venv/bin/activate
python main.py
```

### Frontend Development
```bash
cd frontend
npm start
# Opens http://localhost:4200 with hot reload
```

## Code Style

### Backend (Python)
- Follow PEP 8 conventions
- Use type hints in function signatures
- Add docstrings to functions

### Frontend (TypeScript/Angular)
- Follow Angular style guide
- Use strict TypeScript mode
- Implement OnInit/OnDestroy lifecycle hooks
- Use services for API calls

## Adding New Features

### Adding a New API Endpoint
1. Define the route in `backend/main.py`
2. Add Pydantic models in `backend/models.py` if needed
3. Update `frontend/src/app/services/*.service.ts`
4. Create/update Angular components as needed

### Adding a New Angular Component
```bash
# Generate component
ng generate component path/component-name

# Generated files:
# - component-name.component.ts
# - component-name.component.html
# - component-name.component.scss
# - component-name.component.spec.ts
```

## Database Changes

### Adding a New Table
1. Create migration in `database/`
2. Update `database/init.sql`
3. Create SQLAlchemy models in `backend/models.py`

## Testing

### Backend Unit Tests
```bash
cd backend
pip install pytest
pytest
```

### Frontend Unit Tests
```bash
cd frontend
npm test
```

### Integration Testing
```bash
docker-compose up
# Run tests against live services
```

## Deployment

### Development (Mac Mini)
```bash
./setup.sh
# Terminal 1: backend
# Terminal 2: frontend
```

### Staging/Production
```bash
docker-compose up -d
```

### Environment Variables
- Copy `.env.example` to `.env`
- Update database credentials
- Update API URLs for production
- Change SECRET_KEY in production

## Git Workflow

1. Create feature branch: `git checkout -b feature/feature-name`
2. Make changes and test
3. Commit with meaningful messages: `git commit -m "Add feature description"`
4. Push to remote: `git push origin feature/feature-name`
5. Create Pull Request
6. Get code review
7. Merge to main

## Common Tasks

### Add Authentication to a Route
```python
from fastapi import Depends
from backend.database import get_db

@app.get("/protected")
async def protected_route(db = Depends(get_db)):
    # Add token validation here
    pass
```

### Add File Upload Support
```python
from fastapi import File, UploadFile

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    # Handle file upload
    pass
```

### Call API from Angular Component
```typescript
constructor(private cadService: CadService) {}

ngOnInit() {
  this.cadService.getJobs().subscribe({
    next: (data) => { this.jobs = data; },
    error: (err) => { console.error(err); }
  });
}
```

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (needs 3.9+)
- Check port 8000 is available: `lsof -i :8000`
- Activate virtual environment: `source venv/bin/activate`

### Frontend build errors
- Clear node_modules: `rm -rf node_modules && npm install`
- Clear Angular cache: `rm -rf .angular`
- Check Node version: `node --version` (needs 18+)

### Database connection issues
- Check PostgreSQL is running: `brew services list`
- Verify credentials in `.env`
- Check DATABASE_URL format

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Angular Documentation](https://angular.io/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

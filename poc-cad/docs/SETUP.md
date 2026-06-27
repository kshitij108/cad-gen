# CAD Generation Platform - Setup Guide

## Prerequisites
- macOS (Mac Mini)
- Homebrew
- Node.js 18+
- Python 3.9+
- PostgreSQL 13+

## Installation

### 1. Install Dependencies via Homebrew
```bash
# Install Homebrew (if not present)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install node       # For Angular CLI and frontend
brew install python     # For FastAPI backend
brew install postgresql # For database
```

### 2. Backend Setup (FastAPI)
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your configuration

# Run the server
python main.py
# Server will start at http://localhost:8000
```

### 3. Database Setup
```bash
cd database

# Create PostgreSQL database
createdb cad_platform

# Initialize schema
psql cad_platform < init.sql
```

### 4. Frontend Setup (Angular)
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
# Application will be available at http://localhost:4200
```

## Project Structure

```
poc-cad/
├── backend/                 # FastAPI application
│   ├── main.py             # Main application file
│   ├── requirements.txt     # Python dependencies
│   └── .env.example        # Environment configuration template
│
├── frontend/               # Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── pages/
│   │   │   │   ├── login/
│   │   │   │   ├── register/
│   │   │   │   └── dashboard/
│   │   │   ├── services/
│   │   │   │   ├── auth.service.ts
│   │   │   │   └── cad.service.ts
│   │   │   └── components/
│   │   ├── main.ts
│   │   └── styles.scss
│   ├── angular.json
│   ├── package.json
│   ├── tailwind.config.js
│   └── tsconfig.json
│
├── database/               # Database configuration
│   └── init.sql           # Schema initialization script
│
└── docs/                   # Documentation
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login
- `POST /auth/forgot-password` - Request password reset

### CAD Generation
- `POST /cad/generate-from-prompt` - Generate CAD from text prompt
- `POST /cad/generate-from-image` - Generate CAD from reference image
- `POST /cad/generate-from-sketch` - Generate CAD from hand-drawn sketch
- `POST /cad/upload-base-model` - Upload existing CAD file
- `GET /cad/job/{job_id}` - Get job status

### Navigation
- `GET /projects` - List all projects
- `GET /spaces` - List all spaces
- `GET /catalogs` - List all catalogs
- `GET /jobs` - List all jobs
- `GET /user/profile` - Get user profile

## Technology Stack

- **Frontend**: Angular 17, Tailwind CSS, TypeScript
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Storage**: Local file system (abstracted for AWS S3 support)

## Development Notes

- Backend runs on port 8000
- Frontend runs on port 4200
- CORS is configured to allow frontend requests
- File uploads are stored in `backend/uploads/`

## Next Steps

1. Implement actual CAD generation AI models
2. Add 3D model viewer component
3. Implement file download functionality
4. Add user authentication with JWT tokens
5. Set up AWS S3 integration for file storage
6. Deploy to production environment

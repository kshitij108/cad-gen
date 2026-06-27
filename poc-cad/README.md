# CAD Generation Platform

A web-based platform for generating manufacturer-ready CAD models from multiple input sources using AI assistance.

## Quick Start

### Prerequisites
- macOS (Mac Mini)
- Homebrew

### Installation
```bash
chmod +x setup.sh
./setup.sh
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Open `http://localhost:4200` in your browser.

## Features

- **Multiple Input Methods**
  - Text prompts for descriptive generation
  - Reference image uploads (JPG/PNG)
  - Hand-drawn sketch uploads
  - Existing CAD file uploads (.STL, .STEP, .OBJ)

- **User Management**
  - Registration with contact and company details
  - Email/Password authentication
  - SSO placeholders (Apple, Google, LinkedIn)
  - Password recovery

- **Dashboard**
  - Project management
  - Spaces for organization
  - Catalogs for templates
  - Job tracking and history

- **CAD Generation**
  - AI-powered generation from various inputs
  - Progress tracking
  - Download final CAD files
  - Access to specification sheets

## Technology Stack

- **Frontend**: Angular 17 + Tailwind CSS
- **Backend**: FastAPI + Python
- **Database**: PostgreSQL
- **Storage**: Local file system (expandable to AWS S3)

## Architecture

The system is built with a modular, API-driven architecture:
- **Frontend** (Angular): Clean, responsive UI with Tailwind styling
- **Backend** (FastAPI): RESTful API handling file uploads and CAD generation
- **Database** (PostgreSQL): User data, project metadata, and file references
- **Storage**: Local filesystem abstracted for cloud expansion

## API Documentation

See [API_DOCS.md](./docs/API_DOCS.md) for detailed endpoint documentation.

## Development Setup

For detailed setup instructions, see [SETUP.md](./docs/SETUP.md).

## Project Structure

```
poc-cad/
├── backend/          # FastAPI application
├── frontend/         # Angular application
├── database/         # Database schema
├── docs/             # Documentation
└── setup.sh          # Quick start script
```

## License

© 2024 CAD Generation Platform

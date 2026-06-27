# API Documentation

## Base URL
- Development: `http://localhost:8000`
- Production: `https://api.cad-platform.com`

## Authentication Endpoints

### Register User
```
POST /auth/register
Content-Type: application/json

{
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "phone": "string",
  "password": "string",
  "company_name": "string",
  "nature_of_business": "string",
  "website": "string (optional)",
  "address": "string (optional)"
}

Response (201):
{
  "status": "success",
  "message": "User registered successfully",
  "user_id": "string"
}
```

### Login
```
POST /auth/login
Content-Type: application/json

{
  "email": "string",
  "password": "string"
}

Response (200):
{
  "status": "success",
  "access_token": "string",
  "token_type": "bearer"
}
```

### Forgot Password
```
POST /auth/forgot-password
Content-Type: application/json

{
  "email": "string"
}

Response (200):
{
  "message": "Password reset email sent"
}
```

## CAD Generation Endpoints

### Generate from Prompt
```
POST /cad/generate-from-prompt
Content-Type: application/json
Authorization: Bearer {token}

{
  "prompt": "string"
}

Response (202):
{
  "status": "processing",
  "job_id": "string",
  "message": "CAD generation started from prompt"
}
```

### Generate from Image
```
POST /cad/generate-from-image
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: File (JPG/PNG)

Response (202):
{
  "status": "processing",
  "job_id": "string",
  "file_uploaded": "string"
}
```

### Generate from Sketch
```
POST /cad/generate-from-sketch
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: File (Image)

Response (202):
{
  "status": "processing",
  "job_id": "string",
  "sketch_uploaded": "string"
}
```

### Upload Base CAD Model
```
POST /cad/upload-base-model
Content-Type: multipart/form-data
Authorization: Bearer {token}

file: File (.STL, .STEP, .OBJ)

Response (200):
{
  "status": "success",
  "file_uploaded": "string",
  "supported_formats": [".STL", ".STEP", ".OBJ"]
}
```

### Get Job Status
```
GET /cad/job/{job_id}
Authorization: Bearer {token}

Response (200):
{
  "job_id": "string",
  "status": "processing|completed|failed",
  "progress": 0-100,
  "result_file": "string (optional)",
  "error": "string (optional)"
}
```

## Navigation Endpoints

### List Projects
```
GET /projects
Authorization: Bearer {token}

Response (200):
{
  "projects": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "created_at": "ISO8601"
    }
  ]
}
```

### List Spaces
```
GET /spaces
Authorization: Bearer {token}

Response (200):
{
  "spaces": [...]
}
```

### List Catalogs
```
GET /catalogs
Authorization: Bearer {token}

Response (200):
{
  "catalogs": [...]
}
```

### List Jobs
```
GET /jobs
Authorization: Bearer {token}

Response (200):
{
  "jobs": [...]
}
```

## User Profile

### Get User Profile
```
GET /user/profile
Authorization: Bearer {token}

Response (200):
{
  "user_id": "string",
  "name": "string",
  "email": "string",
  "company_name": "string (optional)"
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

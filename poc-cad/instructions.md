# Project Blueprint: AI-Assisted CAD Generation Platform

## 1. Project Overview
**Objective:** Build a web-based platform that allows users to generate final, manufacturer-ready CAD models (with measurements) from various inputs: text prompts, reference images, hand-drawn sketches, or existing CAD files. 

**Target Environment:** Mac Mini (Local deployment & testing)
**Architecture Style:** Modular, API-driven (separating UI from the heavy AI/CAD generation backend).

## 2. Tech Stack Recommendations
* **Frontend:** Angular (with Tailwind CSS for replicating the clean, minimalist UI in the mockups).
* **Backend / API:** Python (FastAPI) — Ideal for handling file uploads (images, CAD), bridging to AI generation models, and processing data pipelines.
* **Database:** PostgreSQL (for user data, project metadata, and file references).
* **Storage:** Local file system for initial Mac Mini testing, abstracted to support AWS S3 or similar for production CAD file storage.

## 3. Core Features & UI Mapping
Based on the provided design screenshots, the system must include:

### A. Authentication Module
* **Sign In Screen:** Email/Password authentication, plus placeholders for SSO (LinkedIn, Apple, Google). Include an "I forgot my password" flow.
* **Registration Screen:** * Contact Details: First Name, Last Name, Email, Phone, Password.
    * Company Details: Company Name, Nature of Business (Dropdown), Website, Phone, Address.

### B. Main Dashboard (The Workspace)
* **Header:** Simple navigation (Projects, Spaces, Catalogs, Jobs) and User Profile icon.
* **Input Area ("Hey there, [Name]"):** A drag-and-drop zone with selectable input modes:
    1.  **Prompt:** Text input for descriptive generation.
    2.  **Reference:** Image upload (JPG/PNG).
    3.  **Sketch:** Hand-drawn image upload.
    4.  **CAD:** Base 3D model upload (.STL, .STEP, .OBJ).
* **Output Area (Post-Processing):** Display the generated 3D model viewer, download links for the final CAD file, and a spec sheet with measurements.

## 4. Mac Mini Environment Setup (Prerequisites)
Instruct the AI to assume the following commands will be run on macOS:
```bash
# Install Homebrew (if not present)
/bin/bash -c "$(curl -fsSL [https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh](https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh))"

# Install dependencies
brew install node       # For Angular CLI and frontend
brew install python     # For FastAPI backend
brew install postgresql # For database
# Care-AI

Care-AI is a student career guidance platform built for engineering students. It combines Firebase Authentication, Firestore, a Flask-based prediction API, traditional machine learning models, and an AI Copilot assistant to help students understand which path currently fits them best:

- Placement
- Higher studies
- Entrepreneurship
- Needs training first

The system supports two separate roles:

- `student`: fills profile data, gets predictions, saves history, and chats with Career Copilot
- `admin`: monitors the student population through a real-time Firestore dashboard

## Core Features

- Firebase email/password authentication
- Role-based access using Firestore user documents
- Student profile form with editable saved history
- ML-based career prediction API
- Skill-gap analysis and recommendations
- Student dashboard with saved attempts and personalized guidance
- Admin dashboard with segmentation, risk alerts, and analytics
- AI Copilot using Groq through an OpenAI-compatible API
- Real-time dashboard updates with Firestore `onSnapshot()`

## System Architecture

```text
┌──────────────────────────────────────────────────────────────┐
│                         Frontend (HTML/JS)                  │
│                                                              │
│  Student Login / Register / Profile / Dashboard              │
│  Admin Login / Admin Dashboard                               │
│                                                              │
│  - Firebase Auth in browser                                  │
│  - Firestore reads/writes in browser                         │
│  - Calls Flask only for AI/ML APIs                           │
└──────────────────────────────────────────────────────────────┘
                           │
                           │ Firebase Auth token
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                      Flask Backend API                       │
│                                                              │
│  /api/predict                                                │
│  /api/copilot                                                │
│  /health                                                     │
│                                                              │
│  - Verifies Firebase ID token using Firebase Admin SDK       │
│  - Loads CSV data and trains models at startup               │
│  - Generates career prediction + recommendations             │
│  - Sends student context to Groq for Copilot replies         │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                 ML + Logic Layer (Python)                    │
│                                                              │
│  DataCollector -> DataCleaner -> ModelTrainer                │
│                              -> CareerPredictor              │
│                              -> GapAnalyzer                  │
│                              -> StudentProfiler              │
└──────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌──────────────────────────────────────────────────────────────┐
│                     Data / External Services                 │
│                                                              │
│  - Firestore: users, students, student_predictions           │
│  - Firebase Auth: login and role-based access                │
│  - Groq API: AI Copilot responses                            │
│  - CSV datasets: academic, career, psychometric             │
└──────────────────────────────────────────────────────────────┘
```

## Current Project Structure

```text
projects/
├── app.py
├── requirements.txt
├── config.yaml
├── firebase-service-account.json      # local only, not committed
├── .env                               # local only, not committed
├── data/
│   └── raw/
│       ├── academic_records.csv
│       ├── career_choices.csv
│       └── psychometric_scores.csv
├── src/
│   ├── dashboard/
│   │   └── student_profiler.py
│   ├── data_processing/
│   │   ├── data_cleaner.py
│   │   └── data_collector.py
│   ├── ml_models/
│   │   ├── gap_analyzer.py
│   │   ├── predictor.py
│   │   └── trainer.py
│   └── utils/
│       └── config.py
├── static/
│   ├── assets/
│   │   ├── logo.png
│   │   └── veltech.jpg
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── dashboard.js
│       └── firebase.js
└── templates/
    ├── student-login.html
    ├── student-register.html
    ├── student-profile.html
    ├── student-dashboard.html
    ├── admin-login.html
    └── admin-dashboard.html
```

## Role-Based Frontend Flow

### Student Flow

1. Student registers in `student-register.html`
2. Firebase Auth creates the account
3. Firestore creates `users/{uid}` with `role: "student"`
4. Student verifies email and logs in
5. Student fills `student-profile.html`
6. Frontend calls `POST /api/predict`
7. Prediction result is saved into:
   - `student_predictions` for version history
   - `students/{uid}` for latest admin-facing record
8. Student lands on `student-dashboard.html`
9. Student can:
   - review prediction history
   - edit previous submissions
   - delete old submissions
   - chat with AI Copilot

### Admin Flow

1. Admin logs in through `admin-login.html`
2. Frontend validates that `users/{uid}.role === "admin"`
3. `admin-dashboard.html` listens to Firestore `students` collection
4. Dashboard updates automatically in real time

## Backend API

### `POST /api/predict`

Authenticated endpoint for career prediction.

Responsibilities:

- verifies Firebase bearer token
- converts student form input into model-ready features
- predicts:
  - placement probability
  - higher studies probability
  - entrepreneurship score
- runs student profiling logic
- returns:
  - `most_likely_path`
  - `recommended_focus_path` internally in logic layer
  - `skill_gaps`
  - `recommendations`

### `POST /api/copilot`

Authenticated endpoint for AI guidance.

Responsibilities:

- verifies Firebase bearer token
- accepts a student question plus latest saved record
- builds a grounded prompt from the student’s real profile
- sends the request to Groq
- returns a natural-language answer for the student dashboard

### `GET /health`

Returns status flags for:

- Firebase initialization
- prediction system initialization
- Copilot configuration
- SDK availability

## Machine Learning and Decision Logic

The current backend logic is intentionally split into two layers:

### 1. ML prediction layer

Placement and higher studies use trained ML models from the CSV dataset.

### 2. decision and recommendation layer

`StudentProfiler` converts raw scores into an interpretable result.

Current behavior:

- `placement_probability` and `higher_studies_probability` come from trained models
- `entrepreneurship_score` is calculated from entrepreneurial traits and academics
- `most_likely_path` can be:
  - `placement`
  - `higher_studies`
  - `entrepreneurship`
  - `needs_training`

### Why `needs_training` exists

The app does not force a polished path when the student profile is weak. It now classifies `needs_training` when:

- the top normalized score is too low
- the student is academically high-risk
- the student’s relevant skill readiness is still weak

### Entrepreneurship logic

Entrepreneurship is not treated like a standard probability from the model. It is currently derived from:

- leadership
- innovation
- risk management
- networking
- communication
- plus smaller academic influence from:
  - CGPA
  - aptitude
  - internship duration
- with arrears penalty

This keeps entrepreneurship from being over-inflated by marks alone.

## Firestore Data Model

### `users`

Document ID: Firebase `uid`

Example:

```json
{
  "name": "Harsha",
  "email": "harsha@veltech.edu.in",
  "role": "student",
  "createdAt": "server timestamp"
}
```

Admin example:

```json
{
  "name": "Admin User",
  "email": "admin@veltech.edu.in",
  "role": "admin"
}
```

### `student_predictions`

Stores full per-submission history for each student.

Example:

```json
{
  "uid": "firebase-user-id",
  "student_name": "Harsha",
  "email": "harsha@veltech.edu.in",
  "cgpa": 9.1,
  "arrears_count": 0,
  "aptitude_score": 88,
  "internship_duration": 4,
  "skills": {
    "programming": 8,
    "communication": 7,
    "problem_solving": 8
  },
  "prediction": {
    "placement_probability": 0.78,
    "higher_studies_probability": 0.31,
    "entrepreneurship_score": 7.5,
    "most_likely_path": "placement",
    "recommendations": []
  },
  "createdAt": "server timestamp"
}
```

### `students`

Stores the latest student snapshot used by the admin dashboard.

Example:

```json
{
  "name": "Harsha",
  "email": "harsha@veltech.edu.in",
  "cgpa": 9.1,
  "arrears_count": 0,
  "aptitude_score": 88,
  "internship_duration": 4,
  "skills": {
    "programming": 8,
    "communication": 7,
    "problem_solving": 8
  },
  "prediction": {
    "career": "placement",
    "placement_probability": 0.78,
    "higher_studies_probability": 0.31
  },
  "createdAt": "server timestamp",
  "updatedAt": "server timestamp"
}
```

## Admin Dashboard Logic

The admin dashboard listens to Firestore in real time and computes:

- Total students
- Placement count
- Higher studies count
- High-risk count
- Average CGPA

### Student segmentation

Current rules:

- `High Potential`
  - `cgpa > 8` and `programming < 5`
- `Placement Ready`
  - `cgpa > 7` and `programming >= 6`
- `High Risk`
  - `cgpa < 6` or `aptitude_score < 40` or `arrears_count > 2`

### Risk alert rules

Students needing attention are flagged when:

- CGPA < 6
- aptitude < 40
- arrears > 2

## AI Copilot Architecture

The student dashboard includes a floating Copilot panel.

Current implementation:

- frontend sends the student question plus latest saved record
- backend verifies Firebase identity
- backend builds a grounded prompt from real student data
- backend sends the prompt to Groq through the OpenAI-compatible SDK
- frontend renders the answer in a styled assistant UI
- if the AI route fails, the dashboard falls back to a local rule-based answer

This means the student still receives guidance even if the external model is unavailable.

## Tech Stack

### Frontend

- HTML
- CSS
- Vanilla JavaScript
- Firebase Auth
- Firestore
- Font Awesome / Boxicons

### Backend

- Python
- Flask
- Flask-CORS
- Firebase Admin SDK
- python-dotenv

### Data / ML

- pandas
- numpy
- scikit-learn
- joblib
- plotly

### AI

- Groq API
- OpenAI-compatible Python SDK

## Configuration

### 1. Python dependencies

Install:

```bash
.venv-mac/bin/python -m pip install -r requirements.txt
```

### 2. Firebase Admin service account

Place your Firebase service account file in the project root:

```text
firebase-service-account.json
```

Or set:

```bash
export FIREBASE_SERVICE_ACCOUNT=/full/path/to/firebase-service-account.json
```

### 3. Environment variables

Create `.env` in the project root:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL=openai/gpt-oss-20b
```

Do not commit secrets.

For local static preview on `http://127.0.0.1:3000`, the student pages automatically call the Flask API on `http://127.0.0.1:5000`.

## How to Run the Project

### Start the backend

```bash
.venv-mac/bin/python app.py
```

Backend URL:

```text
http://127.0.0.1:5000
```

### Start the frontend

Serve the project root:

```bash
python3 -m http.server 3000
```

Frontend URLs:

- `http://127.0.0.1:3000/templates/student-login.html`
- `http://127.0.0.1:3000/templates/student-register.html`
- `http://127.0.0.1:3000/templates/admin-login.html`

## Firebase Security Rules

The current frontend expects Firestore access for:

- `users`
- `student_predictions`
- `students`

Use rules that support:

- students reading and writing only their own records
- admins reading everything they need
- role validation through `users/{uid}.role`

## Testing Checklist

### Student

1. Register with `@veltech.edu.in`
2. Verify email
3. Login successfully
4. Submit profile form
5. Confirm prediction saved in `student_predictions`
6. Confirm latest snapshot saved in `students/{uid}`
7. Open student dashboard
8. Try edit, delete, and Copilot

### Admin

1. Ensure a `users/{uid}` doc exists with `role: "admin"`
2. Login via `admin-login.html`
3. Open admin dashboard
4. Confirm:
   - student count
   - risk alerts
   - segmentation
   - table filters
   - live Firestore updates

## Notes and Design Decisions

- Flask does not render the frontend pages
- frontend pages are static and client-driven
- Firebase handles authentication in the browser
- Firestore is the source of truth for saved student data
- Flask is used only for prediction and AI assistance
- student history and admin summary are stored separately for cleaner UX and faster queries

## Known Improvements for Future Work

- move Firebase config into one shared pattern across all pages
- add export/download for admin reports
- add more robust logging and request tracing
- add unit tests for predictor and profiler logic
- add production deployment setup for Flask and static hosting
- add model versioning and analytics audit trail

## Recruiter-Friendly Deployment

The strongest public setup for this project is:

- `Firebase Hosting` for the public website
- `Cloud Run` for the Flask backend
- `Firebase Auth` and `Firestore` for authentication and live data

This gives you:

- a fast public website
- HTTPS automatically
- a clean architecture you can explain in interviews
- a professional custom domain later if you want one

### Architecture

```text
Recruiter Browser
      |
      v
Firebase Hosting
  - /student-login
  - /student-register
  - /student-profile
  - /student-dashboard
  - /admin-login
  - /admin-dashboard
      |
      v
Hosting rewrite for /api/*
      |
      v
Cloud Run Flask API
  - /api/predict
  - /api/copilot
  - /health
      |
      +--> Firebase Admin
      +--> Groq API
      +--> CSV-trained ML models
```

### What Was Added For Deployment

- `Dockerfile` for Cloud Run
- `gunicorn` in `requirements.txt`
- support for `FIREBASE_SERVICE_ACCOUNT_JSON` in cloud environments
- configurable CORS using `FRONTEND_ORIGIN` or `CORS_ORIGINS`
- `firebase.json` with Hosting rewrites to Cloud Run
- `static/js/app-config.js` so local development and hosted deployment both work

### Before You Start

You need:

1. a GitHub account
2. a Firebase project
3. a Google Cloud project linked to the same Firebase project
4. billing enabled on Google Cloud because Cloud Run requires it
5. the Firebase CLI installed
6. the Google Cloud CLI installed

### Step 1. Put The Project On GitHub

Create a new repository on GitHub, then push this project.

Example:

```bash
git init
git add .
git commit -m "Prepare Care-AI for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/care-ai.git
git push -u origin main
```

### Step 2. Create A Production Service Account

In Firebase or Google Cloud:

1. open `Project settings`
2. open `Service accounts`
3. generate a new private key
4. keep the JSON file safe

For Cloud Run, copy the full JSON content because the backend now supports:

- `FIREBASE_SERVICE_ACCOUNT_JSON`

That is easier than uploading a file to the server.

### Step 3. Set Up Cloud Run

Build and deploy from this project folder:

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud run deploy care-ai-api \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated
```

When prompted for environment variables, add:

- `GROQ_API_KEY`
- `GROQ_BASE_URL=https://api.groq.com/openai/v1`
- `GROQ_MODEL=openai/gpt-oss-20b`
- `FIREBASE_SERVICE_ACCOUNT_JSON=<paste the full JSON on one line>`
- `FRONTEND_ORIGIN=https://YOUR_PROJECT_ID.web.app`
- `CORS_ORIGINS=https://YOUR_PROJECT_ID.web.app,https://YOUR_PROJECT_ID.firebaseapp.com`

After deploy, test:

```text
https://YOUR_CLOUD_RUN_URL/health
```

### Step 4. Set Up Firebase Hosting

Login and initialize Hosting:

```bash
firebase login
firebase use YOUR_PROJECT_ID
firebase init hosting
```

Use these answers:

- public directory: `.`
- single-page app: `No`
- overwrite files: `No`

This repository already includes a `firebase.json` configured to:

- serve the HTML pages from `templates/`
- rewrite `/api/**` to the Cloud Run service `care-ai-api`
- expose cleaner public paths like `/student-login`

Deploy Hosting:

```bash
firebase deploy --only hosting
```

### Step 5. Add Authorized Domains In Firebase Auth

In Firebase Console:

1. go to `Authentication`
2. open `Settings`
3. add these domains:
   - `YOUR_PROJECT_ID.web.app`
   - `YOUR_PROJECT_ID.firebaseapp.com`
4. later add your custom domain too

### Step 6. Check Firestore Rules

Before you show this publicly, make sure Firestore rules only allow:

- students to read and write their own data
- admins to read dashboard collections

If Firestore rules are too open, recruiters could accidentally see insecure data handling.

### Step 7. Optional Custom Domain

For a stronger recruiter impression, connect a custom domain in Firebase Hosting:

- `careai-demo.in`
- `careaiapp.tech`
- `yourname-care-ai.dev`

After connecting the domain:

1. add it in Firebase Hosting
2. update Firebase Auth authorized domains
3. update Cloud Run env vars:
   - `FRONTEND_ORIGIN=https://your-domain.com`
   - `CORS_ORIGINS=https://your-domain.com,https://YOUR_PROJECT_ID.web.app`

### What To Tell Recruiters

Use a short explanation like this:

`Care-AI is deployed with Firebase Hosting for the public frontend and Google Cloud Run for the Flask ML API. Authentication and real-time student/admin data are handled with Firebase Auth and Firestore, while the backend verifies Firebase tokens and serves prediction and AI guidance APIs securely.`

### Demo Checklist Before Sharing

1. open the public URL in an incognito window
2. test student registration and login
3. submit a profile and verify prediction works
4. open student dashboard and test Copilot
5. log in as admin and verify dashboard data loads
6. confirm `/health` is healthy
7. check browser console for errors
8. verify no localhost URLs remain in the UI

### Important Production Note

The backend currently retrains ML models during startup. That is okay for a project demo, but not ideal for larger production traffic because startup becomes slower. A future improvement is:

- train once offline
- save models with `joblib`
- load them on startup instead of retraining

## Free Deployment With Render

If you want a fully free recruiter demo without enabling Google Cloud billing, use:

- `Render` to host the full Flask app
- `Firebase Auth` and `Firestore` exactly as they are now
- the free Render subdomain such as `https://care-ai.onrender.com`

This is the simplest path because the Flask app already serves the pages and APIs together.

### Why This Path

- no Google Cloud billing setup required
- one deployment instead of separate frontend and backend deployments
- still public and professional enough for recruiter sharing
- works well for demo traffic

### Render Files In This Repo

- `render.yaml` for one-click Render settings
- `requirements.txt` includes `gunicorn`
- backend supports `FIREBASE_SERVICE_ACCOUNT_JSON` for cloud secrets

### Render Setup

In Render, create a `Web Service` from this GitHub repo and use:

- Runtime: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Plan: `Free`

### Render Environment Variables

Add these in the Render dashboard:

- `GROQ_API_KEY`
- `GROQ_BASE_URL=https://api.groq.com/openai/v1`
- `GROQ_MODEL=openai/gpt-oss-20b`
- `FIREBASE_SERVICE_ACCOUNT_JSON=<paste the Firebase service account JSON as one line>`

### Firebase Auth Change For Render

After Render gives you a public URL, add that domain in Firebase Authentication:

1. open Firebase Console
2. Authentication
3. Settings
4. Authorized domains
5. add your Render domain, for example `care-ai.onrender.com`

### Important Limitation

Render free instances can sleep after inactivity, so the first request may be slow. That is normal for a free demo and acceptable for recruiter sharing if you mention it only when needed.

### Free Custom Domain Note

A custom domain is not free. If you want the deployment itself to stay fully free, use the free Render domain first. If you later decide to spend a little for polish, you can buy a custom domain and connect it to Render.

## Authoring Notes

This README reflects the current implemented project state in this repository, including:

- student/admin split
- Firebase + Firestore architecture
- Flask API-only backend
- Groq-powered Copilot
- current ML + recommendation logic

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

## Authoring Notes

This README reflects the current implemented project state in this repository, including:

- student/admin split
- Firebase + Firestore architecture
- Flask API-only backend
- Groq-powered Copilot
- current ML + recommendation logic

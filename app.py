import json
import os
import sys
import pandas as pd
import firebase_admin
from firebase_admin import auth, credentials
from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv

try:
    from openai import OpenAI
    from openai import APIStatusError
except ImportError:
    OpenAI = None
    APIStatusError = None

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.data_processing.data_collector import DataCollector
from src.data_processing.data_cleaner import DataCleaner
from src.ml_models.trainer import ModelTrainer
from src.ml_models.predictor import CareerPredictor
from src.ml_models.gap_analyzer import GapAnalyzer
from src.dashboard.student_profiler import StudentProfiler

app = Flask(__name__)

load_dotenv()

collector = None
cleaner = None
trainer = None
predictor = None
gap_analyzer = None
profiler = None
openai_client = None
system_initialized = False


def get_cors_origins():
    raw_origins = os.getenv('CORS_ORIGINS', '').strip()
    if not raw_origins:
        frontend_origin = os.getenv('FRONTEND_ORIGIN', '').strip()
        if frontend_origin:
            raw_origins = frontend_origin

    origins = [origin.strip() for origin in raw_origins.split(',') if origin.strip()]
    return origins or '*'


CORS(app, resources={r"/api/*": {"origins": get_cors_origins()}})


def get_openai_client():
    global openai_client

    if openai_client is not None:
        return openai_client, None

    if OpenAI is None:
        return None, 'OpenAI SDK is not installed. Run pip install -r requirements.txt.'

    api_key = os.getenv('GROQ_API_KEY', '').strip()
    if not api_key:
        return None, 'GROQ_API_KEY is not configured on the backend.'

    openai_client = OpenAI(
        api_key=api_key,
        base_url=os.getenv('GROQ_BASE_URL', 'https://api.groq.com/openai/v1')
    )
    return openai_client, None


def build_copilot_prompt(question, record, user_email):
    prediction = record.get('prediction', {}) if isinstance(record, dict) else {}
    recommendations = prediction.get('recommendations', []) if isinstance(prediction, dict) else []
    top_recommendations = recommendations[:3] if isinstance(recommendations, list) else []

    context_lines = [
        f"Student email: {user_email or 'unknown'}",
        f"Student name: {record.get('student_name') or record.get('name') or 'Student'}",
        f"CGPA: {record.get('cgpa', 'unknown')}",
        f"Arrears count: {record.get('arrears_count', 'unknown')}",
        f"Aptitude score: {record.get('aptitude_score', 'unknown')}",
        f"Internship duration: {record.get('internship_duration', 'unknown')}",
        f"Most likely path: {prediction.get('most_likely_path') or prediction.get('career') or 'unknown'}",
        f"Placement probability: {prediction.get('placement_probability', 'unknown')}",
        f"Higher studies probability: {prediction.get('higher_studies_probability', 'unknown')}",
        f"Entrepreneurship score (0-10): {prediction.get('entrepreneurship_score', 'unknown')}",
        f"Top recommendations: {top_recommendations if top_recommendations else 'none'}",
    ]

    system_prompt = (
        "You are Career Copilot for Care-AI, helping Indian engineering students understand their "
        "career prediction results. Give practical, supportive advice in plain English. Use only the "
        "student context provided. Do not invent grades, scores, or history. Keep answers concise, "
        "specific, and action-oriented. When the profile looks weak, explain the gap honestly and suggest "
        "the next 2-4 steps. If the user asks for a study or preparation plan, give a short structured plan."
    )

    user_prompt = (
        "Student context:\n"
        + "\n".join(context_lines)
        + "\n\nStudent question:\n"
        + question.strip()
    )

    return system_prompt, user_prompt


def initialize_firebase():
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT', 'firebase-service-account.json')
    service_account_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON', '').strip()

    if firebase_admin._apps:
        return True

    if service_account_json:
        try:
            credential_info = json.loads(service_account_json)
        except json.JSONDecodeError:
            print("FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON.")
            return False
        credential = credentials.Certificate(credential_info)
    else:
        if not os.path.exists(service_account_path):
            print(f"Firebase service account file not found: {service_account_path}")
            print("Set FIREBASE_SERVICE_ACCOUNT_JSON, set FIREBASE_SERVICE_ACCOUNT, or place firebase-service-account.json in the project root.")
            return False
        credential = credentials.Certificate(service_account_path)

    firebase_admin.initialize_app(credential)
    return True


def initialize_system():
    global collector, cleaner, trainer, predictor, gap_analyzer, profiler, system_initialized

    if system_initialized:
        return

    print("Initializing Care-AI API...")

    collector = DataCollector()
    cleaner = DataCleaner()
    trainer = ModelTrainer()

    academic_data = collector.load_academic_data()
    career_data = collector.load_career_data()
    psychometric_data = collector.load_psychometric_data()

    merged_data = collector.merge_datasets(academic_data, career_data, psychometric_data)

    categorical_cols = ['department', 'region', 'gender']
    numeric_cols = ['cgpa', 'arrears_count', 'internship_duration', 'aptitude_score']
    cleaned_data = cleaner.preprocess_data(merged_data, categorical_cols, numeric_cols)

    features = cleaned_data[numeric_cols + categorical_cols]
    placement_target = cleaned_data['placement_status']
    higher_studies_target = cleaned_data['higher_studies_choice']

    trainer.train_placement_model(features, placement_target)
    trainer.train_higher_studies_model(features, higher_studies_target)

    predictor = CareerPredictor(trainer)

    skill_requirements = {
        'placement': {
            'programming': 7,
            'communication': 8,
            'problem_solving': 8,
            'teamwork': 7
        },
        'higher_studies': {
            'research': 8,
            'analytical_thinking': 9,
            'writing': 8,
            'subject_knowledge': 9
        },
        'entrepreneurship': {
            'leadership': 9,
            'innovation': 8,
            'risk_management': 7,
            'networking': 8
        }
    }

    gap_analyzer = GapAnalyzer(skill_requirements)
    profiler = StudentProfiler(predictor, gap_analyzer)
    system_initialized = True
    print("Care-AI API initialized successfully.")


def initialize_application():
    firebase_ready = initialize_firebase()
    initialize_system()
    if not firebase_ready:
        print("Starting without Firebase Admin. Authenticated API calls will fail until credentials are configured.")


initialize_application()


def verify_firebase_user():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, ('Missing bearer token', 401)

    token = auth_header.split('Bearer ', 1)[1].strip()
    if not token:
        return None, ('Missing bearer token', 401)

    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token, None
    except Exception:
        return None, ('Invalid token', 401)


@app.get('/')
def index():
    return redirect(url_for('student_login_page'))


@app.get('/student-login')
def student_login_page():
    return render_template('student-login.html')


@app.get('/student-register')
def student_register_page():
    return render_template('student-register.html')


@app.get('/student-profile')
def student_profile_page():
    return render_template('student-profile.html')


@app.get('/student-dashboard')
def student_dashboard_page():
    return render_template('student-dashboard.html')


@app.get('/admin-login')
def admin_login_page():
    return render_template('admin-login.html')


@app.get('/admin-dashboard')
def admin_dashboard_page():
    return render_template('admin-dashboard.html')


@app.post('/api/predict')
def predict_career():
    if profiler is None:
        return jsonify({'success': False, 'error': 'Prediction system is not initialized'}), 503

    user, error = verify_firebase_user()
    if error:
        message, status = error
        return jsonify({'success': False, 'error': message}), status

    try:
        data = request.get_json(silent=True) or {}

        student_data = pd.DataFrame({
            'cgpa': [float(data.get('cgpa', 0))],
            'arrears_count': [int(data.get('arrears_count', 0))],
            'internship_duration': [int(data.get('internship_duration', 0))],
            'aptitude_score': [int(data.get('aptitude_score', 0))],
            'department': [int(data.get('department', 1))],
            'region': [int(data.get('region', 1))],
            'gender': [int(data.get('gender', 0))]
        })

        student_skills = {
            'programming': int(data.get('programming', 5)),
            'communication': int(data.get('communication', 5)),
            'problem_solving': int(data.get('problem_solving', 5)),
            'teamwork': int(data.get('teamwork', 5)),
            'research': int(data.get('research', 5)),
            'analytical_thinking': int(data.get('analytical_thinking', 5)),
            'writing': int(data.get('writing', 5)),
            'subject_knowledge': int(data.get('subject_knowledge', 5)),
            'leadership': int(data.get('leadership', 5)),
            'innovation': int(data.get('innovation', 5)),
            'risk_management': int(data.get('risk_management', 5)),
            'networking': int(data.get('networking', 5))
        }

        profile = profiler.generate_student_profile(student_data, student_skills)

        return jsonify({
            'success': True,
            'uid': user['uid'],
            'student_name': data.get('student_name', 'Student'),
            'predictions': {
                'placement_probability': float(profile['predictions']['placement_probability']),
                'higher_studies_probability': float(profile['predictions']['higher_studies_probability']),
                'entrepreneurship_score': float(profile['predictions']['entrepreneurship_score'])
            },
            'most_likely_path': profile['most_likely_path'],
            'skill_gaps': profile['skill_gaps'],
            'recommendations': profile['recommendations']
        })
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.post('/api/copilot')
def copilot_answer():
    user, error = verify_firebase_user()
    if error:
        message, status = error
        return jsonify({'success': False, 'error': message}), status

    payload = request.get_json(silent=True) or {}
    question = str(payload.get('question', '')).strip()
    if not question:
        return jsonify({'success': False, 'error': 'Question is required.'}), 400

    client, client_error = get_openai_client()
    if client_error:
        return jsonify({'success': False, 'error': client_error}), 503

    record = payload.get('latestRecord') or {}
    if not isinstance(record, dict):
        record = {}

    try:
        system_prompt, user_prompt = build_copilot_prompt(question, record, user.get('email', ''))
        response = client.responses.create(
            model=os.getenv('GROQ_MODEL', os.getenv('OPENAI_MODEL', 'openai/gpt-oss-20b')),
            input=[
                {
                    'role': 'system',
                    'content': [
                        {
                            'type': 'input_text',
                            'text': system_prompt
                        }
                    ]
                },
                {
                    'role': 'user',
                    'content': [
                        {
                            'type': 'input_text',
                            'text': user_prompt
                        }
                    ]
                }
            ]
        )

        answer = getattr(response, 'output_text', '') or ''
        answer = answer.strip()
        if not answer:
            return jsonify({'success': False, 'error': 'OpenAI returned an empty response.'}), 502

        return jsonify({
            'success': True,
            'answer': answer,
            'model': os.getenv('GROQ_MODEL', os.getenv('OPENAI_MODEL', 'openai/gpt-oss-20b'))
        })
    except Exception as exc:
        if APIStatusError is not None and isinstance(exc, APIStatusError):
            status_code = getattr(exc, 'status_code', None) or 500
            if status_code == 429:
                return jsonify({
                    'success': False,
                    'error': 'Groq quota is unavailable right now. Check billing, limits, or model access, then try again.'
                }), 429
            if status_code == 401:
                return jsonify({
                    'success': False,
                    'error': 'Groq authentication failed. Check the backend API key.'
                }), 401

            return jsonify({
                'success': False,
                'error': f'Groq request failed with status {status_code}.'
            }), status_code
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.get('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'firebase_initialized': bool(firebase_admin._apps),
        'prediction_system_initialized': profiler is not None,
        'copilot_configured': bool(os.getenv('GROQ_API_KEY', '').strip()),
        'copilot_sdk_ready': OpenAI is not None
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', '5000')))


#cd"/Users/harshachinthala/Documents/Major Project/projects"
# .venv/bin/python app.py


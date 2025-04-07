#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import uuid
import psycopg2
import logging

# Configuration des logs
logging.basicConfig(
    filename='/var/log/coursero_api.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
CORS(app)  # Active CORS pour toutes les routes

# Configuration de la base de données
DB_CONFIG = {
    "host": "192.168.159.229",  # IP du Master DB
    "database": "coursero",
    "user": "coursero",
    "password": "coursero_secure_password"
}

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'})

@app.route('/api/auth/register', methods=['POST'])
def register():
    try:
        data = request.json
        required_fields = ['email', 'password', 'full_name']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        user_id = str(uuid.uuid4())
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (id, email, password, full_name) VALUES (%s, %s, %s, %s)",
            (user_id, data['email'], data['password'], data['full_name'])
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "User registered successfully", "user_id": user_id})
    except psycopg2.IntegrityError:
        return jsonify({"error": "Email already exists"}), 409
    except Exception as e:
        logging.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, email FROM users WHERE email = %s AND password = %s",
            (data['email'], data['password'])
        )

        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return jsonify({
                "message": "Login successful",
                "user_id": user[0],
                "email": user[1]
            })
        else:
            return jsonify({"error": "Invalid credentials"}), 401
    except Exception as e:
        logging.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/api/courses', methods=['GET'])
def get_courses():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT course_id, course_name FROM courses")
        courses = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(courses)
    except Exception as e:
        logging.error(f"Error getting courses: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/exercises', methods=['GET'])
def get_exercises():
    course_id = request.args.get('course_id')
    if not course_id:
        return jsonify({"error": "course_id is required"}), 400

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT exercise_id, exercise_name FROM exercises WHERE course_id = %s",
            (course_id,)
        )
        exercises = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(exercises)
    except Exception as e:
        logging.error(f"Error getting exercises: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/languages', methods=['GET'])
def get_languages():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT language_id, language_name FROM languages")
        languages = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return jsonify(languages)
    except Exception as e:
        logging.error(f"Error getting languages: {str(e)}")
        return jsonify({"error": "Database error"}), 500

@app.route('/api/submit', methods=['POST'])
def submit():
    try:
        data = request.json
        logging.info(f"Received submission: {data}")

        required_fields = ['user_id', 'course_id', 'exercise_id', 'language_id', 'code']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        submission_id = str(uuid.uuid4())
        data['submission_id'] = submission_id

        with open(f'/var/queue/coursero/{submission_id}.json', 'w') as f:
            json.dump(data, f)

        logging.info(f"Queued submission {submission_id}")
        return jsonify({'status': 'queued', 'submission_id': submission_id})
    except Exception as e:
        logging.error(f"Error processing submission: {str(e)}")
        return jsonify({"error": "Submission failed"}), 500

@app.route('/api/status/<submission_id>', methods=['GET'])
def status(submission_id):
    try:
        if os.path.exists(f'/var/queue/coursero/{submission_id}.json'):
            return jsonify({'status': 'queued'})

        if os.path.exists(f'/var/processing/coursero/{submission_id}.json'):
            return jsonify({'status': 'processing'})

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT status, score, details FROM submissions WHERE submission_id = %s",
            (submission_id,)
        )
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result:
            return jsonify({
                'status': result[0],
                'score': result[1],
                'details': result[2]
            })

        return jsonify({'status': 'not_found'})
    except Exception as e:
        logging.error(f"Error checking status: {str(e)}")
        return jsonify({"error": "Status check failed"}), 500

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.submission_id, c.course_name, e.exercise_name, s.status,
                   s.score, s.submit_time, s.details
            FROM submissions s
            JOIN exercises e ON s.exercise_id = e.exercise_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE s.user_id = %s
            ORDER BY s.submit_time DESC
        """, (user_id,))

        submissions = [{
            'submission_id': row[0],
            'course_name': row[1],
            'exercise_name': row[2],
            'status': row[3],
            'score': row[4],
            'submit_time': row[5].isoformat(),
            'details': row[6]
        } for row in cursor.fetchall()]

        cursor.close()
        conn.close()
        return jsonify(submissions)
    except Exception as e:
        logging.error(f"Error getting submissions: {str(e)}")
        return jsonify({"error": "Failed to get submissions"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

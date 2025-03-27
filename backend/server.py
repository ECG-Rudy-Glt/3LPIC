#
# @author GAULT Rudy
# @company Cloud Temple
# @created_at 2025-03-27 10:15:00
# @updated_by GAULT Rudy
# @updated_at 2025-03-27 21:38:12
#

import os
import json
import flask
from flask import Flask, request, jsonify
from flask_cors import CORS
import werkzeug.utils
import tempfile
import uuid
import hashlib
import jwt
import datetime
from functools import wraps

from app import CourserEvaluator
from db.database import Database
from flask import send_from_directory
# Initialisation de l'application Flask - DÉPLACÉ ICI
app = Flask(__name__)
CORS(app)  # Activer CORS pour permettre les requêtes depuis le frontend

# Clé secrète pour JWT
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'votre_clé_secrète_temporaire')
app.config['SECRET_KEY'] = SECRET_KEY

# Ajouter cette route - APRÈS la définition de app
@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'authentication.html')

# Pour servir les fichiers statiques (js, css)
@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(os.path.join('../frontend', path)):
        return send_from_directory('../frontend', path)
    return "Not Found", 404

# Initialiser l'évaluateur et la base de données
evaluator = CourserEvaluator()
db = Database()

# Répertoire pour les uploads temporaires
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Fonction de décoration pour vérifier le token JWT
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Récupérer le token depuis les headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        
        try:
            # Décoder le token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user_id']
        except:
            return jsonify({'message': 'Token invalide ou expiré'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Route pour l'authentification
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Données manquantes'}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({'message': 'Email et mot de passe requis'}), 400
    
    # TODO: Implémenter la vérification du mot de passe avec la base de données
    # Pour l'instant, nous utilisons un utilisateur de démonstration
    if email == 'demo@coursero.com' and password == 'password':
        # Générer un token JWT valide pendant 24 heures
        token = jwt.encode({
            'user_id': 'demo123',
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")
        
        return jsonify({
            'token': token,
            'user': {
                'id': 'demo123',
                'email': email,
                'fullName': 'Utilisateur Démo'
            }
        }), 200
    
    return jsonify({'message': 'Identifiants incorrects'}), 401

# Ajouter après la route de login

# Route pour l'inscription
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Données manquantes'}), 400
    
    email = data.get('email')
    password = data.get('password')
    full_name = data.get('fullName')
    
    if not email or not password or not full_name:
        return jsonify({'message': 'Tous les champs sont requis'}), 400
    
    # Vérifier si l'utilisateur existe déjà
    if db.user_exists(email):
        return jsonify({'message': 'Cet email est déjà utilisé'}), 400
    
    # Hachage du mot de passe avant stockage
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    # Générer un ID utilisateur unique
    user_id = str(uuid.uuid4())
    
    # Enregistrer l'utilisateur dans la base de données
    db.create_user(user_id, email, hashed_password, full_name)
    
    # Générer un token JWT pour l'authentification automatique
    token = jwt.encode({
        'user_id': user_id,
        'email': email,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    
    return jsonify({
        'message': 'Inscription réussie',
        'token': token,
        'user': {
            'id': user_id,
            'email': email,
            'fullName': full_name
        }
    }), 201

# Route pour récupérer les cours disponibles
@app.route('/api/courses', methods=['GET'])
@token_required
def get_courses(current_user):
    courses = db.get_available_courses()
    return jsonify(courses), 200

# Route pour récupérer les exercices d'un cours
@app.route('/api/exercises', methods=['GET'])
@token_required
def get_exercises(current_user):
    course_id = request.args.get('courseId')
    if not course_id:
        return jsonify({'message': 'ID de cours requis'}), 400
    
    exercises = db.get_exercises_for_course(course_id)
    return jsonify(exercises), 200

# Route pour récupérer les soumissions d'un utilisateur
@app.route('/api/submissions', methods=['GET'])
@token_required
def get_submissions(current_user):
    submissions = db.get_user_submissions(current_user)
    return jsonify({'submissions': submissions}), 200

# Route pour soumettre un code
@app.route('/api/submit', methods=['POST'])
@token_required
def submit_code(current_user):
    # Vérifier que le fichier est présent
    if 'file' not in request.files:
        return jsonify({'message': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    course_id = request.form.get('courseId')
    exercise_id = request.form.get('exerciseId')
    language = request.form.get('language')
    
    if not file or not course_id or not exercise_id or not language:
        return jsonify({'message': 'Données manquantes'}), 400
    
    # Vérifier l'extension du fichier
    allowed_extensions = {
        'python': '.py',
        'c': '.c'
    }
    
    if not file.filename.endswith(allowed_extensions.get(language, '')):
        return jsonify({'message': f'Format de fichier invalide pour {language}'}), 400
    
    # Sauvegarder le fichier temporairement
    filename = werkzeug.utils.secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(file_path)
    
    # Soumettre le code pour évaluation
    evaluator.submit_code(current_user, course_id, exercise_id, language, file_path)
    
    return jsonify({
        'message': 'Code soumis avec succès',
        'status': 'pending'
    }), 202

# Démarrer le serveur s'il est exécuté directement
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
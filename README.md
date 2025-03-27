# Coursero - Système d'évaluation automatique de code

Coursero est une plateforme d'évaluation automatique de code permettant aux étudiants de soumettre leurs exercices de programmation et de recevoir un feedback instantané.

## Installation sous WSL (Windows Subsystem for Linux)

### Prérequis

- WSL2 installé sur Windows
- Ubuntu 20.04 LTS ou plus récent comme distribution Linux
- Droits administrateur sur WSL

### 1. Mise à jour du système

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Installation des dépendances

```bash
# Installation des paquets système nécessaires
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib apache2 libapache2-mod-wsgi-py3 openssl

# Activer les modules Apache nécessaires
sudo a2enmod ssl proxy proxy_http rewrite
```

### 3. Configuration de PostgreSQL

```bash
# Démarrer PostgreSQL
sudo systemctl start postgresql

# Créer la base de données et l'utilisateur
sudo -u postgres psql -c "CREATE DATABASE coursero;"
sudo -u postgres psql -c "CREATE USER coursero WITH PASSWORD 'coursero_secure_password';"
sudo -u postgres psql -c "ALTER ROLE coursero SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE coursero SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE coursero SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE coursero TO coursero;"
```

### 4. Installation de l'application

```bash
# Cloner le dépôt (si vous utilisez Git)
# git clone https://github.com/votre-repo/coursero.git
# cd coursero

# Ou naviguez vers le répertoire du projet si vous l'avez déjà
cd /home/rudy/3lpic/3LPIC

# Créer un environnement virtuel Python
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances Python
pip install flask flask-cors psycopg2-binary bcrypt werkzeug

# Créer les répertoires nécessaires pour les uploads
mkdir -p backend/uploads
sudo chown -R $USER:$USER backend/uploads

# Initialiser la base de données avec les tables et données initiales
cd backend/db
python init_db.py
cd ../..
```

### 5. Configuration Apache (optionnel pour le déploiement en production)

```bash
# Créer un fichier de configuration Apache
sudo tee /etc/apache2/sites-available/coursero.conf > /dev/null << 'EOF'
<VirtualHost *:80>
    ServerName coursero.local
    Redirect permanent / https://coursero.local/
</VirtualHost>

<VirtualHost *:443>
    ServerName coursero.local
    
    SSLEngine on
    SSLCertificateFile      /etc/ssl/certs/coursero.crt
    SSLCertificateKeyFile   /etc/ssl/private/coursero.key
    
    DocumentRoot /home/rudy/3lpic/3LPIC/frontend
    
    <Directory /home/rudy/3lpic/3LPIC/frontend>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^(.*)$ /authentication.html [L]
    </Directory>
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    <Location /api>
        ProxyPass http://localhost:5000/api
        ProxyPassReverse http://localhost:5000/api
    </Location>
    
    ErrorLog ${APACHE_LOG_DIR}/coursero-error.log
    CustomLog ${APACHE_LOG_DIR}/coursero-access.log combined
</VirtualHost>
EOF

# Générer un certificat SSL auto-signé
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/coursero.key \
  -out /etc/ssl/certs/coursero.crt \
  -subj "/C=FR/ST=Paris/L=Paris/O=Coursero/CN=coursero.local"

# Activer le site et redémarrer Apache
sudo a2ensite coursero.conf
sudo systemctl restart apache2

# Ajouter une entrée dans /etc/hosts
echo "127.0.0.1 coursero.local" | sudo tee -a /etc/hosts
```

### 6. Lancement de l'application en mode développement

```bash
# Activer l'environnement virtuel si ce n'est pas déjà fait
source venv/bin/activate

# Démarrer le serveur backend
cd backend
python server.py
```

L'application sera accessible à l'adresse http://localhost:5000 ou https://coursero.local si vous avez configuré Apache.

## Utilisation

1. Accédez à la page d'accueil et créez un compte
2. Connectez-vous avec vos identifiants
3. Soumettez votre code pour un exercice spécifique
4. Visualisez vos résultats dans le tableau de bord

## Administration de la base de données

### Démarrer PostgreSQL
```bash
sudo systemctl start postgresql
```

### Arrêter PostgreSQL
```bash
sudo systemctl stop postgresql
```

### Redémarrer PostgreSQL
```bash
sudo systemctl restart postgresql
```

### Se connecter à la base de données
```bash
sudo -u postgres psql -d coursero
```

### Réinitialiser les tables de la base de données
```bash
cd /home/rudy/3lpic/3LPIC
source venv/bin/activate
cd backend/db
python init_db.py
```

## Dépannage

### Si PostgreSQL ne démarre pas
```bash
sudo systemctl status postgresql
sudo journalctl -xeu postgresql
```

### Problèmes de permission
```bash
sudo chown -R postgres:postgres /var/lib/postgresql
sudo systemctl restart postgresql
```

### Réinitialisation complète de la base de données
```bash
sudo -u postgres dropdb coursero
sudo -u postgres createdb coursero
cd /home/rudy/3lpic/3LPIC
source venv/bin/activate
cd backend/db
python init_db.py
```

## Développement

Pour installer les dépendances de développement et contribuer au projet :

```bash
pip install pytest coverage pylint
```

Pour exécuter les tests :
```bash
cd backend
pytest
```

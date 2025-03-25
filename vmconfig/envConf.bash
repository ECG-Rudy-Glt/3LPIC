#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installation du système d'évaluation de code Coursero${NC}"
echo "-------------------------------------------------------------------------"

# Vérification des droits d'administrateur
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Erreur: Ce script doit être exécuté en tant qu'administrateur (sudo)${NC}"
  exit 1
fi

# Création des répertoires
echo -e "${YELLOW}Création des répertoires...${NC}"
mkdir -p /var/www/coursero/frontend
mkdir -p /var/www/coursero/backend/uploads
mkdir -p /etc/ssl/coursero

# Installation des dépendances
echo -e "${YELLOW}Installation des dépendances...${NC}"
apt-get update
apt-get install -y apache2 python3 python3-pip postgresql postgresql-contrib libapache2-mod-wsgi-py3 openssl

# Activer les modules Apache nécessaires
echo -e "${YELLOW}Configuration d'Apache...${NC}"
a2enmod ssl
a2enmod proxy
a2enmod proxy_http
a2enmod rewrite

# Générer un certificat SSL auto-signé
echo -e "${YELLOW}Génération d'un certificat SSL auto-signé...${NC}"
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/coursero.key \
  -out /etc/ssl/certs/coursero.crt \
  -subj "/C=FR/ST=Paris/L=Paris/O=Coursero/CN=coursero.local"

# Configuration de PostgreSQL
echo -e "${YELLOW}Configuration de PostgreSQL...${NC}"
sudo -u postgres psql -c "CREATE DATABASE coursero;"
sudo -u postgres psql -c "CREATE USER coursero WITH PASSWORD 'coursero_secure_password';"
sudo -u postgres psql -c "ALTER ROLE coursero SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE coursero SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE coursero SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE coursero TO coursero;"

# Configuration des variables d'environnement
echo -e "${YELLOW}Configuration des variables d'environnement...${NC}"
cat > /etc/environment <<EOF
DB_NAME=coursero
DB_USER=coursero
DB_PASSWORD=coursero_secure_password
DB_HOST=localhost
DB_PORT=5432
EOF

# Installation des dépendances Python
echo -e "${YELLOW}Installation des dépendances Python...${NC}"
pip3 install flask flask-cors psycopg2-binary bcrypt werkzeug

# Copier les fichiers de l'application
echo -e "${YELLOW}Copie des fichiers de l'application...${NC}"
cp -r /path/to/frontend/* /var/www/coursero/frontend/
cp -r /path/to/backend/* /var/www/coursero/backend/

# Copier la configuration Apache
cp /path/to/coursero.conf /etc/apache2/sites-available/

# Activer le site
a2ensite coursero.conf

# Redémarrer Apache
systemctl restart apache2

echo -e "${GREEN}Installation terminée !${NC}"
echo "Ajoutez 'coursero.local' à votre fichier /etc/hosts:"
echo "127.0.0.1 coursero.local"
echo ""
echo "Pour démarrer le backend, exécutez:"
echo "cd /var/www/coursero/backend && python3 server.py"
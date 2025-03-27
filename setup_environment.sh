#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Configuration de l'environnement pour Coursero${NC}"
echo "-------------------------------------------------------------------"

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 n'est pas installé. Veuillez l'installer avant de continuer.${NC}"
    exit 1
fi

# Vérifier si pip est installé
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}pip3 n'est pas détecté, tentative d'installation...${NC}"
    sudo apt update
    sudo apt install -y python3-pip
fi

# Vérifier si venv est installé
if ! python3 -m venv --help &> /dev/null; then
    echo -e "${YELLOW}Module venv non détecté, tentative d'installation...${NC}"
    sudo apt update
    sudo apt install -y python3-venv
fi

# Créer l'environnement virtuel s'il n'existe pas
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Création de l'environnement virtuel...${NC}"
    python3 -m venv venv
    
    if [ ! -d "venv" ]; then
        echo -e "${RED}Échec de la création de l'environnement virtuel.${NC}"
        exit 1
    fi
fi

# Activer l'environnement virtuel
echo -e "${YELLOW}Activation de l'environnement virtuel...${NC}"
source venv/bin/activate

# Vérifier si l'activation a réussi
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}Échec de l'activation de l'environnement virtuel.${NC}"
    exit 1
fi

# Installer les dépendances nécessaires
echo -e "${YELLOW}Installation des dépendances Python...${NC}"
pip install flask flask-cors psycopg2-binary bcrypt werkzeug PyJWT

# Créer les répertoires nécessaires pour les uploads
mkdir -p backend/uploads
sudo chown -R $USER:$USER backend/uploads

echo -e "${GREEN}Configuration de l'environnement terminée avec succès !${NC}"
echo ""
echo -e "Pour activer l'environnement virtuel, exécutez: ${YELLOW}source venv/bin/activate${NC}"
echo -e "Pour initialiser la base de données, exécutez: ${YELLOW}cd backend/db && python init_db.py${NC}"
echo -e "Pour démarrer le serveur, exécutez: ${YELLOW}cd backend && python server.py${NC}"

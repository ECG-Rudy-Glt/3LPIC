#!/bin/bash

# Rendre le script d'initialisation exécutable
chmod +x /home/rudy/3lpic/3LPIC/backend/db/init_db.py

# Exécuter le script d'initialisation
cd /home/rudy/3lpic/3LPIC/backend/db
python3 init_db.py

echo "Script d'initialisation de la base de données exécuté"

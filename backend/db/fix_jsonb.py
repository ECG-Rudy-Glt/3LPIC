#!/usr/bin/env python3

import os
import psycopg2

# Récupérer les informations de connexion depuis les variables d'environnement
db_name = os.environ.get('DB_NAME', 'coursero')
db_user = os.environ.get('DB_USER', 'coursero')
db_password = os.environ.get('DB_PASSWORD', 'coursero_secure_password')
db_host = os.environ.get('DB_HOST', 'localhost')
db_port = os.environ.get('DB_PORT', '5432')

print(f"Tentative de connexion à la base de données {db_name}...")
conn = psycopg2.connect(
    dbname=db_name,
    user=db_user,
    password=db_password,
    host=db_host,
    port=db_port
)

# Vérifier si la version de PostgreSQL supporte JSONB
cur = conn.cursor()
cur.execute("SELECT version();")
version = cur.fetchone()[0]
print(f"Version PostgreSQL: {version}")

# Pour les versions qui ne supportent pas JSONB (< 9.4), utiliser JSON
if "9.3" in version or "9.2" in version or "9.1" in version or "9.0" in version:
    print("Cette version de PostgreSQL ne supporte pas JSONB, utilisation de JSON à la place...")
    
    # Correction de la table submissions
    try:
        cur.execute("""
        ALTER TABLE submissions 
        ALTER COLUMN details TYPE JSON USING details::JSON;
        """)
        conn.commit()
        print("Table 'submissions' modifiée pour utiliser JSON au lieu de JSONB")
    except Exception as e:
        conn.rollback()
        print(f"Erreur lors de la modification de la table: {e}")
else:
    print("La version de PostgreSQL supporte JSONB, aucune correction nécessaire")

conn.close()
print("Opération terminée")

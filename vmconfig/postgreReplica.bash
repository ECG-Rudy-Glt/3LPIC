#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Configuration de la haute disponibilité pour Coursero${NC}"
echo "-------------------------------------------------------------------"

# Vérification des droits d'administrateur
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Erreur: Ce script doit être exécuté en tant qu'administrateur (sudo)${NC}"
  exit 1
fi

# Configuration de la réplication PostgreSQL sur le serveur primaire
setup_primary_db() {
    echo -e "${YELLOW}Configuration du serveur PostgreSQL primaire...${NC}"
    
    # Modifier postgresql.conf
    cat >> /etc/postgresql/12/main/postgresql.conf <<EOF
# Réplication
listen_addresses = '*'
wal_level = replica
max_wal_senders = 10
wal_keep_segments = 64
max_replication_slots = 10
EOF

    # Modifier pg_hba.conf pour autoriser la réplication
    cat >> /etc/postgresql/12/main/pg_hba.conf <<EOF
# Autoriser la réplication depuis le serveur secondaire
host    replication     coursero        192.168.1.0/24           md5
EOF

    # Redémarrer PostgreSQL
    systemctl restart postgresql
    
    # Créer un utilisateur de réplication
    sudo -u postgres psql -c "CREATE USER replicator WITH REPLICATION ENCRYPTED PASSWORD 'secure_replication_password';"
    
    echo -e "${GREEN}Configuration du serveur primaire terminée${NC}"
}

# Configuration de la réplication PostgreSQL sur le serveur secondaire
setup_secondary_db() {
    echo -e "${YELLOW}Configuration du serveur PostgreSQL secondaire...${NC}"
    
    # Arrêter PostgreSQL
    systemctl stop postgresql
    
    # Sauvegarder le répertoire de données existant
    mv /var/lib/postgresql/12/main /var/lib/postgresql/12/main_old
    
    # Créer un nouveau répertoire de données
    mkdir -p /var/lib/postgresql/12/main
    chown postgres:postgres /var/lib/postgresql/12/main
    
    # Effectuer une copie initiale depuis le primaire
    echo -e "${YELLOW}Effectuer une copie initiale depuis le primaire...${NC}"
    sudo -u postgres pg_basebackup -h PRIMARY_IP -D /var/lib/postgresql/12/main -U replicator -P -v
    
    # Créer le fichier de configuration de la réplication
    cat > /var/lib/postgresql/12/main/recovery.conf <<EOF
standby_mode = 'on'
primary_conninfo = 'host=PRIMARY_IP port=5432 user=replicator password=secure_replication_password'
trigger_file = '/tmp/postgresql.trigger'
EOF
    
    chown postgres:postgres /var/lib/postgresql/12/main/recovery.conf
    
    # Redémarrer PostgreSQL
    systemctl start postgresql
    
    echo -e "${GREEN}Configuration du serveur secondaire terminée${NC}"
}

# Configuration de HAProxy pour la répartition de charge
setup_haproxy() {
    echo -e "${YELLOW}Installation et configuration de HAProxy...${NC}"
    
    apt-get install -y haproxy
    
    cat > /etc/haproxy/haproxy.cfg <<EOF
global
    log /dev/log    local0
    log /dev/log    local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # SSL default configuration
    ssl-default-bind-options no-sslv3 no-tlsv10 no-tlsv11
    ssl-default-bind-ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS
    ssl-default-server-ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/coursero.pem
    http-request redirect scheme https code 301 unless { ssl_fc }
    default_backend http_back

backend http_back
    balance roundrobin
    option httpchk HEAD /health HTTP/1.1
    server web1 192.168.1.10:80 check
    server web2 192.168.1.11:80 check

# Interface d'administration (statistiques)
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats realm HAProxy\ Statistics
    stats auth admin:password
EOF

    # Combiner le certificat et la clé pour HAProxy
    cat /etc/ssl/certs/coursero.crt /etc/ssl/private/coursero.key > /etc/ssl/certs/coursero.pem
    chmod 600 /etc/ssl/certs/coursero.pem
    
    # Redémarrer HAProxy
    systemctl restart haproxy
    
    echo -e "${GREEN}Configuration de HAProxy terminée${NC}"
}

# Menu
echo "Que souhaitez-vous configurer?"
echo "1) Serveur PostgreSQL primaire"
echo "2) Serveur PostgreSQL secondaire"
echo "3) HAProxy pour la répartition de charge"
echo "4) Tout configurer"
read -p "Votre choix (1-4): " choice

case $choice in
    1)
        setup_primary_db
        ;;
    2)
        read -p "Adresse IP du serveur primaire: " primary_ip
        # Remplacer PRIMARY_IP par l'adresse IP fournie
        sed -i "s/PRIMARY_IP/$primary_ip/g" "$0"
        setup_secondary_db
        ;;
    3)
        setup_haproxy
        ;;
    4)
        setup_primary_db
        read -p "Adresse IP du serveur primaire: " primary_ip
        # Remplacer PRIMARY_IP par l'adresse IP fournie
        sed -i "s/PRIMARY_IP/$primary_ip/g" "$0"
        setup_secondary_db
        setup_haproxy
        ;;
    *)
        echo -e "${RED}Choix invalide${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Configuration terminée !${NC}"
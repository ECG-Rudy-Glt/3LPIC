#!/bin/bash

# Couleurs pour les messages
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Script de dépannage HAProxy pour Coursero${NC}"
echo "-------------------------------------------------------------------"

# Vérification des droits d'administrateur
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Erreur: Ce script doit être exécuté en tant qu'administrateur (sudo)${NC}"
  exit 1
fi

# Vérifier si HAProxy est installé
if ! command -v haproxy &> /dev/null; then
    echo -e "${YELLOW}HAProxy n'est pas installé. Installation...${NC}"
    apt-get update && apt-get install -y haproxy
else
    echo -e "${GREEN}HAProxy est déjà installé.${NC}"
fi

# Sauvegarde de la configuration actuelle
if [ -f /etc/haproxy/haproxy.cfg ]; then
    echo -e "${YELLOW}Sauvegarde de la configuration actuelle...${NC}"
    cp /etc/haproxy/haproxy.cfg /etc/haproxy/haproxy.cfg.backup
    echo -e "${GREEN}Sauvegarde créée: /etc/haproxy/haproxy.cfg.backup${NC}"
fi

# Créer une configuration minimale fonctionnelle
echo -e "${YELLOW}Création d'une configuration HAProxy minimale...${NC}"
cat > /etc/haproxy/haproxy.cfg << 'EOF'
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log global
    mode http
    option httplog
    option dontlognull
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

frontend http_front
    bind *:80
    default_backend web_back

backend web_back
    balance roundrobin
    server apache1 192.168.159.222:80 check
    server apache2 192.168.159.221:80 check

listen stats
    bind *:8404
    stats enable
    stats uri /
    stats realm HAProxy\ Statistics
    stats auth admin:password
EOF

# Vérifier la configuration
echo -e "${YELLOW}Vérification de la configuration...${NC}"
if haproxy -c -f /etc/haproxy/haproxy.cfg; then
    echo -e "${GREEN}Configuration valide.${NC}"
    
    # Redémarrer HAProxy
    echo -e "${YELLOW}Redémarrage de HAProxy...${NC}"
    systemctl restart haproxy
    
    # Vérifier l'état du service
    if systemctl is-active --quiet haproxy; then
        echo -e "${GREEN}HAProxy a démarré avec succès!${NC}"
        echo "Configuration minimale installée. Vous pouvez maintenant l'améliorer."
    else
        echo -e "${RED}HAProxy n'a pas pu démarrer. Consultez les journaux:${NC}"
        echo "journalctl -xeu haproxy.service"
    fi
else
    echo -e "${RED}La configuration générée contient des erreurs.${NC}"
fi

# Afficher des informations utiles
echo -e "\n${GREEN}Informations utiles:${NC}"
echo "1. Configuration HAProxy: /etc/haproxy/haproxy.cfg"
echo "2. Vérifier la configuration: sudo haproxy -c -f /etc/haproxy/haproxy.cfg"
echo "3. Redémarrer HAProxy: sudo systemctl restart haproxy"
echo "4. Vérifier l'état: sudo systemctl status haproxy"
echo "5. Consulter les logs: sudo journalctl -xeu haproxy.service"
echo "6. Interface d'administration: http://votre-ip:8404/ (login: admin, password: password)"

Voici un tutoriel complet sous forme de README pour configurer HAProxy pour le projet Coursero, incluant l'installation, la génération d'un certificat SSL, la configuration de base et la configuration avancée pour utiliser la bonne IP de serveur backend (192.168.159.220).

---

# Tutoriel de configuration de HAProxy pour le projet Coursero

Ce guide vous accompagne dans l'installation, la configuration et le déploiement de HAProxy avec support SSL pour le projet Coursero.

---

## 1. Installation de HAProxy

Commencez par mettre à jour vos paquets et installer HAProxy :

```bash
sudo apt-get update
sudo apt-get install haproxy
```

---

## 2. Génération du certificat SSL

Avant de configurer HAProxy avec SSL, vous devez générer un certificat.

### Option 1 : Exécution du script de génération

Si un script est déjà prévu, exécutez :

```bash
sudo bash /home/rudy/3lpic/3LPIC/vmconfig/create_ssl_cert.sh
```

### Option 2 : Génération manuelle

Sinon, générez un certificat auto-signé en suivant ces étapes :

1. Créez le répertoire sécurisé pour stocker la clé privée :

   ```bash
   sudo mkdir -p /etc/ssl/private
   sudo chmod 700 /etc/ssl/private
   ```

2. Générez le certificat auto-signé (valable 365 jours) :

   ```bash
   sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
     -keyout /etc/ssl/private/coursero.key \
     -out /etc/ssl/certs/coursero.crt \
     -subj "/C=FR/ST=Paris/L=Paris/O=Coursero/CN=coursero.local"
   ```

3. Créez un fichier PEM regroupant le certificat et la clé (nécessaire pour HAProxy) :

   ```bash
   sudo cat /etc/ssl/certs/coursero.crt /etc/ssl/private/coursero.key > /etc/ssl/certs/coursero.pem
   sudo chmod 600 /etc/ssl/certs/coursero.pem
   ```

---

## 3. Configuration de base de HAProxy

Pour vérifier que HAProxy fonctionne avant de passer à la configuration avancée, vous pouvez commencer par une configuration de test sans SSL.

### a. Configuration de base (sans SSL)

Ouvrez le fichier de configuration :

```bash
sudo nano /etc/haproxy/haproxy.cfg
```

Remplacez le contenu par le bloc suivant :

```ini
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

# Frontend HTTP de base
frontend http_front
    bind *:80
    default_backend web_backend

# Backend principal pour vos serveurs web
backend web_backend
    balance roundrobin
    server apache1 192.168.159.220:80 check

# Interface d'administration
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats realm HAProxy\ Statistics
    stats auth admin:password   # Changez ce mot de passe !
```

Sauvegardez et quittez l’éditeur.  
Pour tester la configuration, exécutez :

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```

Si tout est correct, activez et redémarrez HAProxy :

```bash
sudo systemctl enable haproxy
sudo systemctl restart haproxy
```

Vérifiez l’état du service :

```bash
sudo systemctl status haproxy
```

---

## 4. Configuration avancée avec SSL

Une fois la configuration de base validée, vous pouvez passer à la configuration combinant HTTP et HTTPS avec redirection automatique.

### a. Mise à jour de la configuration

Ouvrez à nouveau le fichier :

```bash
sudo nano /etc/haproxy/haproxy.cfg
```

Remplacez le contenu par :

```ini
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # Paramètres SSL par défaut
    ssl-default-bind-options no-sslv3 no-tlsv10 no-tlsv11
    ssl-default-bind-ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS

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

# Frontend combiné HTTP/HTTPS
frontend main
    # Définir plusieurs ports
    bind *:8800
    bind *:8080
    bind *:443 ssl crt /etc/ssl/certs/coursero.pem

    mode http

    # Rediriger automatiquement vers HTTPS si la connexion n'est pas sécurisée
    http-request redirect scheme https code 301 unless { ssl_fc }

    # ACL pour distinguer le trafic statique
    acl url_static path_beg -i /static /images /javascript /stylesheets
    acl url_static path_end -i .jpg .gif .png .css .js

    # Choix du backend en fonction de l'URL
    use_backend static-backend if url_static
    default_backend app-backend

    # Timeouts spécifiques au frontend
    timeout client 30s
    timeout connect 5s
    timeout server 30s

# Backend pour les applications dynamiques
backend app-backend
    balance roundrobin
    option httpchk GET /health HTTP/1.1
    http-check expect status 200
    server apache1 192.168.159.220:80 check

# Backend pour le contenu statique
backend static-backend
    balance roundrobin
    server apache1 192.168.159.220:80 check

# Interface d'administration
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats realm HAProxy\ Statistics
    stats auth admin:password   # Changez ce mot de passe !
```

> **Remarque :**  
> - Ici, nous utilisons une seule adresse IP (192.168.159.220) pour le serveur backend.  
> - La vérification de santé est configurée pour la route `/health`. Assurez-vous que cette URL existe sur votre serveur et renvoie un code HTTP 200.  
> - La redirection HTTP vers HTTPS s'applique sur les ports 8800 et 8080.

Sauvegardez vos modifications, puis vérifiez la configuration :

```bash
sudo haproxy -c -f /etc/haproxy/haproxy.cfg
```

Si la configuration est valide, redémarrez HAProxy :

```bash
sudo systemctl restart haproxy
```

---

## 5. Vérification du service

Pour vérifier que HAProxy fonctionne correctement, utilisez :

```bash
sudo systemctl status haproxy
```

Vous pouvez également surveiller les logs pour repérer d'éventuelles erreurs :

```bash
sudo journalctl -xeu haproxy.service
sudo tail -f /var/log/haproxy.log
```

---

## 6. Résolution des problèmes

Si HAProxy ne démarre pas ou affiche des erreurs :

1. **Vérifiez la syntaxe de la configuration :**

   ```bash
   sudo haproxy -c -f /etc/haproxy/haproxy.cfg
   ```

2. **Consultez les journaux pour des messages détaillés :**

   ```bash
   sudo journalctl -xeu haproxy.service
   ```

3. **Problèmes fréquents :**

   - **Certificat SSL :** Vérifiez que le fichier `/etc/ssl/certs/coursero.pem` existe et possède les bonnes permissions.
     
     ```bash
     ls -la /etc/ssl/certs/coursero.pem
     ```

   - **Vérification de santé :** Si la route `/health` n'existe pas ou ne renvoie pas le code 200, adaptez le paramétrage dans le backend ou créez une page de santé sur votre serveur.

   - **Connectivité réseau :** Vérifiez que la machine HAProxy peut joindre le serveur backend :
     
     ```bash
     curl http://192.168.159.220/health
     ```
     ou utilisez `telnet`/`nc` pour tester la connexion sur le port 80.

4. **Test de configuration minimale :**

   En dernier recours, testez une configuration de base sans SSL ni vérifications avancées :

   ```bash
   sudo tee /etc/haproxy/haproxy.cfg > /dev/null << 'EOF'
   global
       log /dev/log local0
       user haproxy
       group haproxy
       daemon

   defaults
       log global
       mode http
       timeout connect 5000ms
       timeout client 50000ms
       timeout server 50000ms

   frontend http_front
       bind *:80
       default_backend web_back

   backend web_back
       server apache1 192.168.159.220:80
   EOF

   sudo systemctl restart haproxy
   ```

---

## 7. Surveillance des logs

Pour suivre l'activité de HAProxy en temps réel :

```bash
sudo tail -f /var/log/haproxy.log
```

---

Ce tutoriel vous permet d’installer et de configurer HAProxy pour le projet Coursero en tenant compte d’un environnement backend unique (192.168.159.220) et en activant le support SSL. Adaptez les adresses IP, ports et chemins de certificats en fonction de votre environnement spécifique. N’hésitez pas à consulter les journaux et à tester les connexions pour vérifier que tout fonctionne correctement.
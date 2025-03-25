<VirtualHost *:80>
    ServerName coursero.local
    Redirect permanent / https://coursero.local/
</VirtualHost>

<VirtualHost *:443>
    ServerName coursero.local
    
    # Certificats SSL (à remplacer par les vôtres)
    SSLEngine on
    SSLCertificateFile      /etc/ssl/certs/coursero.crt
    SSLCertificateKeyFile   /etc/ssl/private/coursero.key
    
    # Répertoire racine du frontend
    DocumentRoot /var/www/coursero/frontend
    
    <Directory /var/www/coursero/frontend>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        
        # Pour les SPAs, rediriger les routes non trouvées vers index.html
        RewriteEngine On
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule ^(.*)$ /authentication.html [L]
    </Directory>
    
    # Configuration du proxy pour l'API backend
    ProxyPreserveHost On
    ProxyRequests Off
    
    <Location /api>
        ProxyPass http://localhost:5000/api
        ProxyPassReverse http://localhost:5000/api
    </Location>
    
    # Logs
    ErrorLog ${APACHE_LOG_DIR}/coursero-error.log
    CustomLog ${APACHE_LOG_DIR}/coursero-access.log combined
</VirtualHost>
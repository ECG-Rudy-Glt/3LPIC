[Unit]
Description=Coursero Backend Service
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/coursero/backend
ExecStart=/usr/bin/python3 /var/www/coursero/backend/server.py
Restart=always
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
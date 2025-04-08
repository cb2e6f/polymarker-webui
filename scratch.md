Steps to Set Up a Flask App with Gunicorn and Nginx
1. Update the System

Run the following command to update the system packages:

bash

sudo dnf update -y

2. Install Required Packages

Install Python, pip, and Nginx if they are not already installed on the system:

bash

sudo dnf install python3 python3-pip nginx

3. Create a Virtual Environment

Create and activate a Python virtual environment:

    Note:
    It is recommended to use the /opt folder to store the application and the virtual environment. Other locations can be discussed and considered.
    Also, create a local account to run the server for enhanced security and allow other users to maintain the server. Once the account is created, ask Research Computing to add it to the Puppet manifest so you can sudo su into it.

bash

python3 -m venv venv
source venv/bin/activate

4. Install Flask and Gunicorn

Install Flask and Gunicorn inside the virtual environment:

bash

pip install Flask gunicorn

5. Deploy Your Flask App

Deploy your Flask application in the desired directory (/opt/flask-cross-charging, for example). Ensure that the Flask app is in place.
6. Configure Gunicorn and Create a Systemd Service File

Create a systemd service file for Gunicorn at /etc/systemd/system/<meaningful_name>.service with the following content:

ini

[Unit]
Description=Flask Cross Charging Application
After=network.target

[Service]
User=jicstreamlit  # Replace with your user
WorkingDirectory=/opt/flask-cross-charging  # Replace with your app's directory
Environment="PATH=/opt/flask-cross-charging/venv/bin"  # Replace with the virtualenv path
ExecStart=/opt/flask-cross-charging/venv/bin/gunicorn -w 2 --timeout 600 -b 127.0.0.1:5000 cross-charging:app

[Install]
WantedBy=multi-user.target

    Note:
    Replace the User, WorkingDirectory, Environment, and ExecStart values with the appropriate values for your environment.

7. Start and Enable the Gunicorn Service

Start and enable the Gunicorn service to run at startup:

bash

sudo systemctl start <meaningful_name>.service
sudo systemctl enable <meaningful_name>.service

    Warning:
    Use this code with caution. Make sure the service is configured properly before enabling it.

8. Configure Nginx with SSL

Create a new server block in your Nginx configuration file (e.g., /etc/nginx/conf.d/cross-charging.conf) to proxy requests to the Flask app and enable SSL:

nginx

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name 172.16.4.46;  # Replace with your server's IP or domain

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server configuration
server {
    listen 443 ssl;
    server_name 172.16.4.46;  # Replace with your server's IP or domain

    # SSL certificate and key files
    ssl_certificate /etc/pki/tls/certs/wildcard.informatics.jic.ac.uk/wildcard_informatics_jic_ac_uk_cert_chain.crt;
    ssl_certificate_key /etc/pki/tls/certs/wildcard.informatics.jic.ac.uk/wildcard_informatics_jic_ac_uk.key;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES128-SHA256:ECDHE-RSA-AES256-SHA384';
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://127.0.0.1:5000;  # Port where Gunicorn is running
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if your Flask app uses WebSocket)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}

    Note:
    Replace 172.16.4.46 and other placeholders with the appropriate values for your setup.

9. SSL Certificate Management with Puppet

When using SSL, Puppet is configured to automatically keep SSL certificates updated. If the SSL certificate already exists or has been requested from Research Computing, creating the directory:

bash

/etc/pki/tls/certs/wildcard.informatics.jic.ac.uk/

and running Puppet:

bash

sudo puppet agent -t

will populate the certificate automatically.

If the certificate is not automatically populated, ask Research Computing to add the ssl_update_cert class to your VM's manifest.
10. Restart Nginx

Finally, restart Nginx to apply all the changes:

bash

sudo systemctl restart nginx

--------------------------------------------------------------------------------------------

EXTRA: Non-SSL Nginx Configuration for Flask and Gunicorn

Save the following configuration in a file, such as /etc/nginx/conf.d/flask_app.conf:

nginx

# Non-SSL server configuration
server {
    listen 80;  # Listen on port 80 for HTTP
    server_name your_domain_or_ip;  # Replace with your server's domain or IP address

    location / {
        # Proxy requests to Gunicorn, which is running on localhost on port 5000
        proxy_pass http://127.0.0.1:5000;
        
        # Preserve the original host and client information
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Optional: WebSocket support (if your Flask app uses WebSocket)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}

Explanation of Key Sections

    server { ... } block: Defines the server configuration, listening on port 80 for HTTP traffic.
    proxy_pass http://127.0.0.1:5000;: Forwards incoming requests to the Gunicorn server, which is assumed to be running on localhost at port 5000.
    proxy_set_header directives: Forward headers to preserve the client's original request information and IP address.
    WebSocket Support: Includes headers and settings needed for WebSocket connections if the Flask app requires it.

After saving this configuration, restart Nginx to apply the changes:

bash

sudo systemctl restart nginx
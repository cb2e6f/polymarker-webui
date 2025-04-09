
---

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

---

## Install

An example walkthrough of installation on a fresh install of almalinux 9.

### create user

First we need to create a user to run things:

```shell
sudo luseradd polymarker
```

### install polymarker

Next we require an instance of the polymarker command line application for 
the webui to run this can be done by following the instructions 
[here](https://github.com/cb2e6f/bio-polymarker/blob/master/README.md).



---
### install mariadb

#### add mariadb repo

We need to add mariadbs stuff

```shell
curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | sudo bash -s -- --mariadb-server-version="mariadb-11.4"

```

```shell
sudo dnf install -y MariaDB MariaDB-devel
```

```shell
sudo systemctl enable mariadb
sudo systemctl start mariadb
```

### configure mariadb

```shell
sudo mariadb-secure-installation 
```

```shell
sudo mariadb -u root -p
```


```mariadb
CREATE USER polymarker;
GRANT ALL ON *.* TO 'polymarker';
```

```shell
mariadb -u polymarker -p
```

```mariadb
CREATE DATABASE polymarker_webui;
```


### install nginx

```shell
sudo dnf install -y nginx
```

### configure nginx

### install polymarker-webui

```shell
mkdir sw
cd sw
wget https://github.com/samtools/samtools/releases/download/1.21/samtools-1.21.tar.bz2
tar -xf samtools-1.21.tar.bz2 
cd samtools-1.21/
./configure 
make
sudo make install
cd ../..
```


```shell
sudo dnf install -y python3-devel
```

```shell
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pmwui-0.0.3-py3-none-any.whl
```



### import data


```shell
pmwui init
pmwui add 161010_Chinese_Spring_v1.0_pseudomolecules.yaml 
```


---




[goz24vof@pm ~]$ history 
    2  sudo dnf update
    3  sudo luseradd polymarker
    4  ls /home/
    5  sudo dnf group install -y "Development Tools"
    6  mkdir sw
    7  cd sw
    8  wget https://mafft.cbrc.jp/alignment/software/mafft-7.526-gcc_fc6.x86_64.rpm
    9  sudo dnf install -y ./mafft-7.526-gcc_fc6.x86_64.rpm
   10  wget https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.16.0/ncbi-blast-2.16.0+-1.x86_64.rpm
   11  sudo dnf install -y ./ncbi-blast-2.16.0+-1.x86_64.rpm 
   12  wget https://github.com/primer3-org/primer3/archive/refs/tags/v2.6.1.tar.gz
   13  tar -xf v2.6.1.tar.gz 
   14  ls
   15  cd primer3-2.6.1/src/
   16  make
   17  sudo make install
   18  cd ../..
   19  sudo dnf install -y glib2-devel
   20  wget https://github.com/cb2e6f/exonerate/archive/refs/tags/v2.4.0.tar.gz
   21  tar -xf v2.4.0.tar.gz 
   22  cd exonerate-2.4.0/
   23  ./configure
   24  make
   25  sudo make install
   26  cd ../..
   27  ls
   28  cd
   29  sudo dnf install -y ruby
   30  sudo dnf install -y ncurses-devel
   31  sudo dnf install -y bzip2-devel
   32  sudo gem install --no-user-install rake
   33  man gem
   34  gem --help
   35  gem help
   36  gem help install
   37  sudo gem install --no-user-install bio-polymarker
   38  polymarker.rb 
   39  dnf module list
   40  sudo shutdown -h now
   41  ip add
   42  ls
   43  sudo -i
   44  ls
   45  cd sw/
   46  ls
   47  wget https://github.com/samtools/samtools/releases/download/1.21/samtools-1.21.tar.bz2
   48  ls
   49  tar -xf samtools-1.21.tar.bz2 
   50  cd samtools-1.21/
   51  ./configure 
   52  make
   53  sudo make install
   54  cd ../..
   55  samtools
   56  sudo dnf install -y nginx
   57  sudo vim /etc/systemd/system/polymarker-webui.service
   58  sudo systemctl enable polymarker-webui.service 
   59  sudo systemctl start polymarker-webui.service 
   60  sudo systemctl status polymarker-webui.service 
   61  /home/polymarker/venv/bin/gunicorn
   62  sudo vim /etc/systemd/system/polymarker-webui.service
   63  journalctl 
   64  sudo vim /etc/systemd/system/polymarker-webui.service
   65  journalctl 
   66  sudo systemctl start polymarker-webui.service 
   67  sudo systemctl daemon-reload 
   68  sudo systemctl start polymarker-webui.service 
   69  sudo systemctl status polymarker-webui.service 
   70  journalctl -f
   71  sudo vim /etc/selinux/config 
   72  sudo systemctl disable polymarker-webui.service 
   73  reboot
   74  sudo reboot
   75  ls
   76  cd reference_genomes/
   77  ls
   78  rm -rf Cadenza_EIv1.1/
   79  ls
   80  cd
   81  ls
   82  sudo -i
   83  ls
   84  curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | sudo bash -s -- --mariadb-server-version="mariadb-11.4"
   85  sudo dnf install -y MariaDB MariaDB-devel
   86  sudo mariadb-secure-installation 
   87  sudo systemctl enable mariadb
   88  sudo systemctl start mariadb
   89  sudo mariadb-secure-installation 
   90  sudo mariadb -u root -p
   91  mariadb -u polymarker -p
   92  sudo dnf install -y python3-devel
   93  sudo -i
   94  sudo systemctl enable polymarker-webui.service 
   95  sudo systemctl start polymarker-webui.service 
   96  sudo systemctl status polymarker-webui.service 
   97  journalctl -f
   98  sudo vim /etc/nginx/nginx.conf
   99  sudo systemctl enable nginx.service 
  100  sudo systemctl start nginx.service 
  101  sudo systemctl status nginx.service 
  102  sudo firewall-cmd --permanent --add-service=http
  103  sudo firewall-cmd --permanent --list-all
  104  sudo firewall-cmd --reload
  105  journalctl -f
  106  sudo systemctl status nginx.service 
  107  sudo systemctl status polymarker-webui.service 
  108  mariadb -u polymarker -p
  109  sudo systemctl restart polymarker-webui.service 
  110  sudo systemctl status polymarker-webui.service 
  111  history 
  112  sudo systemctl restart polymarker-webui.service 
  113  ls
  114  l
  115  ls
  116  sudo systemctl status polymarker-webui.service 
  117  journalctl -f
  118  ls
  119  cd ../
  120  ls
  121  ls /tmp/
  122  find . -name log_test
  123  sudo find . -name log_test
  124  sudo systemctl restart polymarker-webui.service 
  125  sudo systemctl status polymarker-webui.service 
  126  sudo systemctl restart polymarker-webui.service 
  127  sudo systemctl status polymarker-webui.service 
  128  journalctl -f
  129  ls
  130  sudo find . -name log_test
  131  sudo systemctl restart polymarker-webui.service 
  132  ps
  133  htop
  134  ls /tmp/
  135  sudo systemctl restart polymarker-webui.service 
  136  ls /tmp/
  137  cat /tmp/1c39bdb8-3c76-4796-ad82-0444d8cf6470.csv 
  138  ls
  139  cd
  140  sudo systemctl restart polymarker-webui.service 
  141  ls
  142  ls /tmp/
  143  ls
  144  sudo systemctl restart polymarker-webui.service 
  145  ls
  146  sudo systemctl restart polymarker-webui.service 
  147  ls
  148  ls /tmp/
  149  rm /tmp/log_test 
  150  sudo systemctl restart polymarker-webui.service 
  151  sudo rm /tmp/log_test 
  152  sudo systemctl restart polymarker-webui.service 
  153  journalctl --unit=gunicorn | tail -n 300
  154  journalctl --unit=polymarker-webui | tail -n 300
  155  sudo vim /etc/systemd/system/polymarker-webui.service 
  156  sudo systemctl restart polymarker-webui.service 
  157  sudo systemctl daemon-reload 
  158  sudo systemctl restart polymarker-webui.service 
  159  journalctl --unit=polymarker-webui
  160  journalctl --unit=polymarker-webui -f
  161  sudo systemctl restart polymarker-webui.service 
  162  journalctl --unit=polymarker-webui -f
  163  sudo systemctl restart polymarker-webui.service 
  164  journalctl --unit=polymarker-webui -f
  165  sudo systemctl restart polymarker-webui.service 
  166  journalctl --unit=polymarker-webui -f
  167  sudo systemctl restart polymarker-webui.service 
  168  journalctl --unit=polymarker-webui -f
  169  sudo systemctl restart polymarker-webui.service 
  170  journalctl --unit=polymarker-webui -f
  171  sudo systemctl restart polymarker-webui.service 
  172  journalctl --unit=polymarker-webui -f
  173  sudo vim /etc/systemd/system/polymarker-webui.service 
  174  which polymarker.rb
  175  ls /usr/local/bin/
  176  sudo vim /etc/systemd/system/polymarker-webui.service 
  177  sudo systemctl restart polymarker-webui.service 
  178  sudo systemctl daemon-reload
  179  sudo systemctl restart polymarker-webui.service 
  180  journalctl --unit=polymarker-webui -f
  181  sudo gem install --no-user-install sorted_set
  182  sudo dnf install ruby-devel
  183  sudo gem install --no-user-install sorted_set
  184  journalctl --unit=polymarker-webui -f
  185  history





(venv) [polymarker@pm ~]$ history 
    1  cd
    2  ls
    3  python -m venv venv
    4  source venv/bin/activate
    5  ls
    6  pip install --upgrade pip
    7  pip list
    8  ls
    9  pip install pmwui-0.0.3-py3-none-any.whl 
   10  ls
   11  mv reference_genomes genomes/
   12  ls
   13  ls genome
   14  ls genomes/
   15  pmwui 
   16  ip add
   17  pip install pmwui-0.0.3-py3-none-any.whl 
   18  pip install pmwui-0.0.3-py3-none-any.whl --force-reinstall
   19  pmwui 
   20  ls
   21  cd genome_configs/
   22  ls
   23  pmwui init
   24  ls ../genomes/
   25  pmwui add 160802_Svevo_v2_pseudomolecules.yaml 
   26  cd
   27  pmwui add 160802_Svevo_v2_pseudomolecules.yaml 
   28  source venv/bin/activate
   29  pmwui add 160802_Svevo_v2_pseudomolecules.yaml 
   30  cd genome_configs/
   31  pmwui add 160802_Svevo_v2_pseudomolecules.yaml 
   32  samtool
   33  samtools
   34  echo $PATH
   35  cd
   36  ls
   37  ls -la
   38  vim .bashrc 
   39  vim .bash_profile 
   40  vim /etc/bashrc 
   41  vim /etc/profile
   42  vim /etc/profile.d/sh.local 
   43  echo $PATH
   44  source venv/bin/activate
   45  ls
   46  cd genome_configs/
   47  ls
   48  pmwui add 160802_Svevo_v2_pseudomolecules.yaml 
   49  ls ../genomes
   50  pmwui add 161010_Chinese_Spring_v1.0_pseudomolecules.yaml 
   51  pmwui add 161010_Chinese_Spring_v1.0_pseudomolecules_tetraploid.yaml 
   52  ls ../genomes
   53  pmwui add Brassica_napus_v4.1.chromosomes.yaml 
   54  ls ../genomes
   55  pmwui add Brassica_rapa.Brapa_1.0.dna_sm.toplevel.yaml 
   56  pmwui
   57  cd
   58  ls
   59  gunicorn -w 2 --timeout 600 -b 127.0.0.1:5000 pwmui:app
   60  gunicorn -w 2 --timeout 600 -b 127.0.0.1:5000 pmwui:app
   61  /home/polymarker/venv/bin/gunicorn
   62  ls
   63  history
   64  source venv/bin/activate
   65  pip install pmwui-0.0.3-py3-none-any.whl --force-reinstall
   66  ls
   67  ls venv/
   68  ls
   69  pip install pmwui-0.0.3-py3-none-any.whl --force-reinstall
   70  ls
   71  pip install pmwui-0.0.3-py3-none-any.whl --force-reinstall
   72  ls
   73* pip install pmwui-0.0.3-py3-n
   74  ls
   75  rm pmwui-0.0.3-py3-none-any.whl 
   76  ls -la
   77  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   78  ls
   79  rm log_test 
   80  ls
   81  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   82  tail -f log
   83  ls
   84  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   85  ls
   86  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   87  ls
   88  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   89  ls
   90  cat polymarker.log 
   91  ls
   92  rm polymarker.log 
   93  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   94  ls
   95  cat polymarker.log 
   96  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
   97  tail polymarker.log 
   98  tail -f polymarker.log 
   99  ls
  100  tail -f polymarker.log 
  101  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
  102  ls
  103  cat polymarker
  104  cat polymarker.log 
  105  rm polymarker1.log 
  106  cat polymarker.log 
  107  ls
  108  cat polymarker1.log 
  109  rm polymarker1.log 
  110  cat polymarker1.log 
  111  cat polymarker.log 
  112  ls
  113  cat polymarker.log 
  114  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
  115  cat polymarker.log 
  116  rm polymarker1.log 
  117  ls
  118  cat polymarker.log 
  119  tail -f polymarker.log 
  120  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
  121  tail -f polymarker.log 
  122  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
  123  polymarker.rb 
  124  pip install --force-reinstall pmwui-0.0.4-py3-none-any.whl 
  125  echo $PATH
  126  history 




[goz24vof@v1389 ~]$ history 
    1  ls
    2  uptime
    3  ls
    4  sudo -i
    5  cd
    6  df -h
    7  history 
    8  ls
    9  ls /home/
   10  sudo -i
   11  ls
   12  cd
   13  ls
   14  sudo luseradd polymarker
   15  ls /home/
   16  sudo dnf group install -y "Development Tools"
   17  mkdir sw
   18  cd sw
   19  wget https://mafft.cbrc.jp/alignment/software/mafft-7.526-gcc_fc6.x86_64.rpm
   20  sudo dnf install -y ./mafft-7.526-gcc_fc6.x86_64.rpm
   21  wget https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.16.0/ncbi-blast-2.16.0+-1.x86_64.rpm
   22  sudo dnf install -y ./ncbi-blast-2.16.0+-1.x86_64.rpm 
   23  wget https://github.com/primer3-org/primer3/archive/refs/tags/v2.6.1.tar.gz
   24  tar -xf v2.6.1.tar.gz 
   25  ls
   26  rm mafft-7.526-gcc_fc6.x86_64.rpm ncbi-blast-2.16.0+-1.x86_64.rpm v2.6.1.tar.gz 
   27  cd ..
   28  ls
   29  rmdir sw/
   30  cd /tmp/
   31  mkdir sw
   32  cd sw/
   33  wget https://github.com/primer3-org/primer3/archive/refs/tags/v2.6.1.tar.gz
   34  tar -xf v2.6.1.tar.gz 
   35  ls
   36  cd primer3-2.6.1/src/
   37  make
   38  sudo make install
   39  cd ../..
   40  sudo dnf install -y glib2-devel
   41  wget https://github.com/cb2e6f/exonerate/archive/refs/tags/v2.4.0.tar.gz
   42  tar -xf v2.4.0.tar.gz 
   43  cd exonerate-2.4.0/
   44  ./configure
   45  make
   46  sudo make install
   47  cd ../..
   48  rm -rf sw
   49  cd
   50  sudo dnf install -y ruby
   51  sudo dnf install -y ncurses-devel
   52  sudo dnf install -y bzip2-devel
   53  sudo gem install --no-user-install rake
   54  sudo -i 
   55  sudo gem install --no-user-install bio-polymarker
   56  sudo -i 
   57  polymarker.rb 
   58  dnf search Mariadb
   59  dnf search MariaDB
   60  dnf module 
   61  dnf module list
   62  dnf search MariaDB
   63  dnf info MariaDB
   64  ls
   65  history 
   66  sudo -i
   67  history 
   68  ls
   69  mkdir sw
   70  cd sw
   71  wget https://github.com/samtools/samtools/releases/download/1.21/samtools-1.21.tar.bz2
   72  tar -xf samtools-1.21.tar.bz2 
   73  cd samtools-1.21/
   74  ./configure 
   75  ls
   76  cd ..
   77  ls
   78  cd ..
   79  ls
   80  mv sw /tmp/
   81  cd /tmp/
   82  cd sw/
   83  ls
   84  cd samtools-1.21/
   85  ./configure 
   86  make
   87  sudo make install
   88  cd 
   89  ls
   90  sudo dnf install -y MariaDB MariaDB-devel
   91  sudo systemctl enable mariadb
   92  sudo systemctl start mariadb
   93  sudo mariadb-secure-installation 
   94  sudo mariadb -u root -p
   95  mariadb -u polymarker -p
   96  sudo dnf install -y nginx
   97  sudo dnf install -y python3-devel
   98  ls
   99  df -h
  100  sudo lvdisplay 
  101  sudo lgdisplay 
  102  sudo vgdisplay 
  103  df -h
  104  htop
  105  sudo lvdisplay 
  106  sudo lvdisplay -a
  107  lsblk
  108  sudo vgdisplay 
  109  sudo lsblk
  110  sudo vgdisplay 
  111  ls
  112  history 




[root@v1389 ~]# history 
    1  ls
    2  cd 
    3  ls
    4  cd /home/
    5  ls
    6  cd ..
    7  ls
    8  gem install --no-user-install rake
    9  gem install --no-user-install bio-polymarker
   10  history 



Status: 2025-04-04 14:21:26 +0100,ERROR The `SortedSet` class has been extracted from the `set` library.You must use the `sorted_set` gem or other alternatives. | Queue length: 0

[goz24vof@pm ~]$ sudo dnf install ruby-devel
[goz24vof@pm ~]$ sudo gem install --no-user-install sorted_set

---

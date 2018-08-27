# Treehouse

# Installation
At a high level, you need to:

 * Install NGINX with RTMP support, from source
 * Set up a MySQL database
 * Install UWSGI
 * Download Treehouse and configure it
 * Configure NGINX and Uwsgi
 * Lock down the server with some firewalls

Install Nginx with RTMP support

    sudo adduser uwsgi
    sudo usermod -aG sudo uwsgi
    sudo su - uwsgi
    sudo apt-get update
    sudo apt-get install build-essential libpcre3 libpcre3-dev libssl-dev zlib1g-dev python3-pip mysql-client mysql-server redis libmysqlclient-dev ffmpeg
    pip3 install uwsgi django mysqlclient redis certbot
    git clone https://github.com/isharacomix/nginx-rtmp-module
    wget http://nginx.org/download/nginx-1.14.0.tar.gz
    tar -xf nginx-1.14.0.tar.gz
    cd nginx-1.14.0
    ./configure --with-http_ssl_module --with-file-aio --add-module=../nginx-rtmp-module
    make -j 1
    sudo make install
    cd ..
    git clone https://github.com/isharacomix/treehouse
    cd treehouse
    cp treehouse/treehouse/_settings.py treehouse/treehouse/settings.py
    sudo mysql
    CREATE USER 'uwsgi'@'localhost';
    CREATE DATABASE treehouse;
    GRANT ALL ON treehouse.* TO "uwsgi"@"localhost";
    EXIT
    sudo mkdir /etc/uwsgi
    sudo mkdir /etc/uwsgi/vassals
    sudo mkdir /var/log/uwsgi
    sudo mkdir /mnt/hls
    sudo chown uwsgi /var/log/uwsgi
    sudo chown uwsgi /mnt/hls
    sudo cp configs/emperor.ini /etc/uwsgi/emperor.ini
    sudo cp configs/treehouse.ini /etc/uwsgi/vassals/treehouse.ini
    sudo cp configs/nginx.service /etc/systemd/system/nginx.service
    sudo cp configs/uwsgi.service /etc/systemd/system/uwsgi.service
    sudo cp configs/nginx.conf /usr/local/nginx/conf/nginx.conf
    cd treehouse

Edit `treehouse/treehouse/settings.py` and change the SECRET KEY and add your
domain or ip address to the ALLOWED_HOSTS.

Make migrations

    python3 manage.py makemigrations application
    python3 manage.py migrate
    python3 manage.py createsuperuser

Configure NGINX - `/usr/local/nginx/conf/nginx.conf`

Specifically, change the STREAMING_KEY. Make up a streaming key like a password
(letters only, no spaces). This will be your secret url for streaming to your
server, something like rtmp://streaming.example.com/STREAMING_KEY/stream

If this key gets compromised or if you need to change it, just change the file
and restart NGINX.

Run daemons and remove uwsgi from sudo.

    sudo service nginx start
    sudo service uwsgi start
    #sudo chmod a+rx /mnt/hls
    exit
    sudo deluser uwsgi sudo

Set up IPtables to protect your server.

    iptables -A INPUT -p tcp --tcp-flags ALL NONE -j DROP
    iptables -A INPUT -p tcp ! --syn -m state --state NEW -j DROP
    iptables -A INPUT -p tcp --tcp-flags ALL ALL -j DROP
    iptables -A INPUT -i lo -j ACCEPT
    iptables -A INPUT -p tcp -m tcp --dport 80 -j ACCEPT
    iptables -A INPUT -p tcp -m tcp --dport 443 -j ACCEPT
    iptables -A INPUT -p tcp -m tcp --dport 22 -j ACCEPT
    iptables -A INPUT -p tcp -m tcp --dport 1935 -j ACCEPT
    iptables -I INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
    iptables -P OUTPUT ACCEPT
    iptables -P INPUT DROP
    sudo apt-get install iptables-persistent

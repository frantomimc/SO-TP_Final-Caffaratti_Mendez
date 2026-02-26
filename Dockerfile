# Usar Debian 11 como base
FROM debian:11-slim

# Instalar Apache, WSGI para Python, Python 3 y pip
RUN apt-get update && apt-get install -y \
    apache2 \
    libapache2-mod-wsgi-py3 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Directorio de trabajo
WORKDIR /var/www/flask-app

# Copiar requerimientos e instalar dependencias usando el pip del sistema
COPY requerimientos.txt .
RUN pip3 install --no-cache-dir -r requerimientos.txt

# Copiar el código de la aplicación
COPY app/ /var/www/flask-app/

# Configurar Apache para que escuche en el puerto 8080
RUN sed -i 's/Listen 80/Listen 8080/' /etc/apache2/ports.conf

# Configurar el VirtualHost de Apache
RUN echo "<VirtualHost *:8080> \n\
    ServerName localhost \n\
    WSGIDaemonProcess flaskapp python-path=/var/www/flask-app \n\
    WSGIProcessGroup flaskapp \n\
    WSGIScriptAlias / /var/www/flask-app/app.wsgi \n\
    <Directory /var/www/flask-app> \n\
        Require all granted \n\
    </Directory> \n\
</VirtualHost>" > /etc/apache2/sites-available/000-default.conf

# Dar permisos a Apache sobre los archivos de la app
RUN chown -R www-data:www-data /var/www/flask-app

# Exponer el puerto
EXPOSE 8080

# Iniciar Apache en primer plano
CMD ["/usr/sbin/apache2ctl", "-D", "FOREGROUND"]
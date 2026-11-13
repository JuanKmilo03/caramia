#!/bin/bash
DB_HOST=${DB_HOST:-db}
DB_PORT=${DB_PORT:-5432}
DB_USER=${DB_USER:-caramia_db_user}
DB_PASSWORD=${DB_PASSWORD:-$DB_PASSWORD}
DB_NAME=${DB_NAME:-caramia_db}
ADMIN_PASSWD=${ADMIN_PASSWD:-tu_clave_maestra_segura}

cat << EOF > /etc/odoo/odoo.conf
[options]
addons_path = /mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
proxy_mode = True
http_port = 10000
db_name = ${DB_NAME}
db_host = ${DB_HOST}
db_port = ${DB_PORT}
db_user = ${DB_USER}
db_password = ${DB_PASSWORD}
db_sslmode = require
limit_time_cpu = 600
limit_time_real = 1200
list_db = False
admin_passwd = ${ADMIN_PASSWD}
EOF

exec "$@"

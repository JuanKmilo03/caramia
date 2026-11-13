FROM odoo:18.0

COPY ./custom_addons /mnt/extra-addons/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo", "-c", "/etc/odoo/odoo.conf"]
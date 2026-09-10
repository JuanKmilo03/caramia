FROM odoo:18.0

USER root

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update && \
    pip install --no-cache-dir --break-system-packages --ignore-installed -r /tmp/requirements.txt && \
    rm -rf /var/lib/apt/lists/* /tmp/requirements.txt

USER odoo
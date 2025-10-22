FROM ghcr.io/home-assistant/aarch64-base:latest
RUN apk add --no-cache python3 py3-paho-mqtt
WORKDIR /opt/supla
COPY supla_autodiscovery.py /opt/supla/supla_autodiscovery.py
COPY rootfs /

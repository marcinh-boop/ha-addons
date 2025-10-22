#!/usr/bin/env python3
import json, os, re, time
import paho.mqtt.client as mqtt
from datetime import datetime

def log(*args):
    print(datetime.now().strftime('[%Y-%m-%d %H:%M:%S]'), *args, flush=True)


OPTS_PATH = "/data/options.json"

def load_options():
    with open(OPTS_PATH, "r") as f:
        o = json.load(f)
    o.setdefault("mqtt_host", "core-mosquitto")
    o.setdefault("mqtt_port", 1883)
    o.setdefault("mqtt_username", "")
    o.setdefault("mqtt_password", "")
    o.setdefault("tls", False)
    o.setdefault("ca_certs", "")
    o.setdefault("supla_prefix", "supla")
    o.setdefault("discovery_prefix", "homeassistant")
    o.setdefault("name_prefix", "Supla")
    o.setdefault("include_devices", [])
    o.setdefault("exclude_devices", [])
    o.setdefault("publish_interval", 0)
    return o

OPTS = load_options()

# mapy jednostek/klas aby HA pokazywał ładne encje
UNIT_MAP = {
    "voltage": ("V", "voltage", "measurement"),
    "current": ("A", "current", "measurement"),
    "power_active": ("W", "power", "measurement"),
    "power_apparent": ("VA", None, "measurement"),
    "power_reactive": ("var", None, "measurement"),
    "frequency": ("Hz", None, "measurement"),
    "power_factor": (None, "power_factor", "measurement"),
    "phase_angle": ("°", None, "measurement"),
    "total_forward_active_energy": ("kWh", "energy", "total_increasing"),
    "total_reverse_active_energy": ("kWh", "energy", "total_increasing"),
    "total_forward_reactive_energy": ("kvarh", None, "total_increasing"),
    "total_reverse_reactive_energy": ("kvarh", None, "total_increasing"),
    "price_per_unit": (None, None, None),
    "total_cost": (None, None, None),
    "total_cost_balanced": (None, None, None),
    "connected": (None, None, None),
    "currency": (None, None, None),
    "support": (None, None, None),
}

TOPIC_RE = re.compile(
    r"^" + re.escape(OPTS["supla_prefix"]) + r"/([^/]+)/devices/(\d+)/channels/(\d+)/state(?:/phases/(\d+))?/([^/]+)$"
)

published_uids = set()

def build_sensor(topic, token, dev, ch, phase, metric):
    key = metric
    uid = f"supla_{dev}_{ch}_{(('p'+phase) if phase else 'p0')}_{key}"
    if uid in published_uids:
        return None, None

    unit, device_class, state_class = UNIT_MAP.get(key, (None, None, "measurement"))
    name_bits = [OPTS["name_prefix"], f"{dev}/{ch}"]
    if phase: name_bits.append(f"F{phase}")
    name_bits.append(key.replace("_"," ").title())
    name = " ".join(name_bits)

    cfg = {
        "name": name,
        "unique_id": uid,
        "state_topic": topic,              # HA czyta bezpośrednio z oryginalnego topicu SUPLA
        "qos": 0,
        "retain": False,
        "device": {
            "identifiers": [f"supla_{dev}"],
            "manufacturer": "SUPLA",
            "model": f"Device {dev} / Channel {ch}",
            "name": f"SUPLA {dev}",
        },
    }
    if unit: cfg["unit_of_measurement"] = unit
    if device_class: cfg["device_class"] = device_class
    if state_class: cfg["state_class"] = state_class

    disc_prefix = OPTS["discovery_prefix"]
    disc_topic = f"{disc_prefix}/sensor/{uid}/config"
    payload = json.dumps(cfg, ensure_ascii=False)
    return disc_topic, payload

def on_connect(client, userdata, flags, rc, properties=None):
    log(f"[supla-autodiscovery] MQTT connected rc={rc}")
    client.subscribe(OPTS["supla_prefix"] + "/#")

def on_message(client, userdata, msg):
    m = TOPIC_RE.match(msg.topic)
    if not m:
        return
    token, dev, ch, phase, metric = m.groups()
    # filtry include/exclude:
    dev_int = int(dev)
    if OPTS["include_devices"] and dev_int not in OPTS["include_devices"]:
        return
    if dev_int in OPTS["exclude_devices"]:
        return

    disc_topic, payload = build_sensor(msg.topic, token, dev, ch, phase, metric)
    if disc_topic:
        client.publish(disc_topic, payload, retain=True)
        published_uids.add(json.loads(payload)["unique_id"])
        log(f"=> discovery: {disc_topic} ({json.loads(payload).get('name')})")

def main():
    log('[supla-autodiscovery] starting...')
    try:
        import paho.mqtt as _m; log(f'[supla-autodiscovery] paho-mqtt: {_m.__version__}')
    except Exception as e:
        log('[supla-autodiscovery] paho version check failed:', e)
    cbv = getattr(mqtt, "CallbackAPIVersion", None)
    if cbv is not None:
        client = mqtt.Client(client_id="supla-autodiscovery", callback_api_version=cbv.VERSION2)
    else:
        client = mqtt.Client(client_id="supla-autodiscovery")

    if OPTS["mqtt_username"] or OPTS["mqtt_password"]:
        client.username_pw_set(OPTS["mqtt_username"], OPTS["mqtt_password"])
    if OPTS["tls"]:
        ca = OPTS.get("ca_certs") or None
        client.tls_set(ca_certs=ca)

    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(OPTS["mqtt_host"], int(OPTS["mqtt_port"]), keepalive=60)
    client.loop_forever()

if __name__ == "__main__":
    main()

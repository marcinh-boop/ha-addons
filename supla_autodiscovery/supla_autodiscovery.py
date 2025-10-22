#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SUPLA → Home Assistant MQTT Discovery
# 1.1.x — LWT/availability + cleanup starych encji + republish

import json
import os
import re
import time
import threading
from datetime import datetime

import paho.mqtt.client as mqtt

# ---------- utils / opcje ----------
def log(*args):
    print(datetime.now().strftime("[%Y-%m-%d %H:%M:%S]"), *args, flush=True)

OPTS_PATH = "/data/options.json"
PUBLISHED_PATH = "/data/published.json"   # uid -> {"disc": "...", "payload": "..."}

def _load_options():
    with open(OPTS_PATH, "r") as f:
        o = json.load(f)

    # MQTT
    o.setdefault("mqtt_host", "core-mosquitto")
    o.setdefault("mqtt_port", 1883)
    o.setdefault("mqtt_username", "")
    o.setdefault("mqtt_password", "")
    o.setdefault("tls", False)
    o.setdefault("ca_certs", "")

    # SUPLA / Discovery
    o.setdefault("supla_prefix", "supla")
    o.setdefault("discovery_prefix", "homeassistant")
    o.setdefault("name_prefix", "Supla")

    # Zachowanie
    o.setdefault("qos", 0)
    o.setdefault("retain", True)
    o.setdefault("include_devices", [])
    o.setdefault("exclude_devices", [])
    o.setdefault("publish_interval", 0)  # minuty; 0 = wył.
    o.setdefault("availability_topic", "supla-autodiscovery/availability")
    o.setdefault("cleanup_delay", 45)    # sekundy po starcie zanim zrobimy cleanup

    return o

OPTS = _load_options()

# ---------- mapy metryk ----------
UNIT_MAP = {
    # energia / moc
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
    # data-sources itp.
    "temperature": ("°C", "temperature", "measurement"),
    "humidity": ("%", "humidity", "measurement"),
    "value": (None, None, "measurement"),
    "on": (None, None, "measurement"),
    "connected": (None, None, "measurement"),
    "price_per_unit": (None, None, None),
    "total_cost": (None, None, None),
    "cost_balanced": (None, None, None),
    "currency": (None, None, None),
    "support": (None, None, None),
}

# supla/<TOKEN>/devices/<DEV>/channels/<CH>/state[/phases/<PHASE>]/<METRIC>
TOPIC_RE = re.compile(
    r"^" + re.escape(OPTS["supla_prefix"]) +
    r"/([^/]+)/devices/(\d+)/channels/(\d+)/state(?:/phases/(\d+))?/([^/]+)$"
)

# runtime:
published_uids = set()           # aby nie dublować podczas pracy
CURRENT = {}                     # uid -> {"disc": "...", "payload": "..."}
try:
    with open(PUBLISHED_PATH, "r") as _f:
        PREV = json.load(_f)     # uid -> {"disc": "..."}
except Exception:
    PREV = {}

log(f"[FILTER] include={sorted(OPTS.get('include_devices', []))} "
    f"exclude={sorted(OPTS.get('exclude_devices', []))}")
log(f"[LWT] availability_topic={OPTS['availability_topic']}  qos={OPTS['qos']} retain={OPTS['retain']}")

# ---------- discovery ----------
def build_sensor(state_topic, token, dev, ch, phase, metric):
    key = metric
    uid = f"supla_{dev}_{ch}_{('p' + phase) if phase else 'p0'}_{key}"
    if uid in published_uids:
        return None, None, None

    # nazwa
    name_bits = [OPTS["name_prefix"], f"{dev}/{ch}"]
    if phase:
        name_bits.append(f"F{phase}")
    name_bits.append(key.replace("_", " ").title())
    name = " ".join(name_bits)

    unit, device_class, state_class = UNIT_MAP.get(key, (None, None, "measurement"))

    cfg = {
        "name": name,
        "unique_id": uid,
        "state_topic": state_topic,                 # HA czyta bezpośrednio z SUPLA
        "qos": int(OPTS["qos"]),
        "retain": bool(OPTS["retain"]),
        "availability_topic": OPTS["availability_topic"],
        "payload_available": "online",
        "payload_not_available": "offline",
        "availability_mode": "latest",
        "device": {
            "identifiers": [f"supla_{dev}"],
            "manufacturer": "SUPLA / ZAMEL",
            "model": f"Device {dev} / Channel {ch}",
            "name": f"{OPTS['name_prefix']} {dev}",
        },
    }
    if unit is not None:
        cfg["unit_of_measurement"] = unit
    if device_class is not None:
        cfg["device_class"] = device_class
    if state_class is not None:
        cfg["state_class"] = state_class

    disc_prefix = OPTS["discovery_prefix"]
    disc = f"{disc_prefix}/sensor/{uid}/config"
    payload = json.dumps(cfg, ensure_ascii=False)

    return uid, disc, payload

# ---------- MQTT callbacks ----------
def on_connect(client, userdata, flags, rc, properties=None):
    log(f"[supla-autodiscovery] MQTT connected rc={rc}")
    # birth
    client.publish(OPTS["availability_topic"], "online", qos=int(OPTS["qos"]), retain=True)
    client.subscribe(OPTS["supla_prefix"] + "/#")

def on_message(client, userdata, msg):
    m = TOPIC_RE.match(msg.topic)
    if not m:
        return
    token, dev, ch, phase, metric = m.groups()

    # filtr include/exclude
    dev_id = int(dev)
    inc = OPTS.get("include_devices", [])
    exc = OPTS.get("exclude_devices", [])
    if inc and dev_id not in inc:
        return
    if dev_id in exc:
        return

    uid, disc, payload = build_sensor(msg.topic, token, dev, ch, phase, metric)
    if not uid:
        return

    # publikacja discovery (retain zawsze True – to konfiguracja)
    client.publish(disc, payload, retain=True, qos=int(OPTS["qos"]))
    published_uids.add(uid)
    CURRENT[uid] = {"disc": disc, "payload": payload}

    try:
        pretty = json.loads(payload).get("name", uid)
    except Exception:
        pretty = uid
    log(f"=> discovery: {disc} ({pretty})")

# ---------- cleanup / republish ----------
def _save_published_snapshot():
    try:
        with open(PUBLISHED_PATH, "w") as f:
            json.dump(CURRENT, f)
    except Exception as e:
        log("[WARN] save published.json failed:", e)

def _cleanup_worker(client):
    # odczekaj aż strumień SUPLA się „rozkręci”
    delay = int(OPTS.get("cleanup_delay", 45))
    time.sleep(max(5, delay))

    old = set(PREV.keys())
    new = set(CURRENT.keys())
    to_del = sorted(list(old - new))

    if to_del:
        log(f"[CLEANUP] removing {len(to_del)} stale entities…")
    removed = 0
    for uid in to_del:
        disc = PREV.get(uid, {}).get("disc")
        if disc:
            client.publish(disc, "", retain=True, qos=int(OPTS["qos"]))
            removed += 1
    if to_del:
        log(f"[CLEANUP] done: removed={removed}")

    _save_published_snapshot()

def _republish_worker(client):
    interval_min = int(OPTS.get("publish_interval", 0))
    if interval_min <= 0:
        return
    while True:
        time.sleep(interval_min * 60)
        items = list(CURRENT.items())
        if not items:
            continue
        log(f"[REPUBLISH] pushing {len(items)} discovery configs…")
        for uid, meta in items:
            client.publish(meta["disc"], meta["payload"], retain=True, qos=int(OPTS["qos"]))
        _save_published_snapshot()

# ---------- main ----------
def main():
    log("[supla-autodiscovery] starting...")
    cbv = getattr(mqtt, "CallbackAPIVersion", None)
    if cbv is not None:
        client = mqtt.Client(client_id="supla-autodiscovery", callback_api_version=cbv.V2)
    else:
        client = mqtt.Client(client_id="supla-autodiscovery")

    # LWT — musi być ustawiony PRZED connect()
    client.will_set(OPTS["availability_topic"], "offline", qos=int(OPTS["qos"]), retain=True)

    if OPTS.get("mqtt_username") or OPTS.get("mqtt_password"):
        client.username_pw_set(OPTS.get("mqtt_username", ""), OPTS.get("mqtt_password", ""))

    if OPTS.get("tls"):
        ca = OPTS.get("ca_certs") or None
        client.tls_set(ca_certs=ca)

    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(OPTS["mqtt_host"], int(OPTS["mqtt_port"]), keepalive=60)

    # wątki serwisowe
    threading.Thread(target=_cleanup_worker, args=(client,), daemon=True).start()
    threading.Thread(target=_republish_worker, args=(client,), daemon=True).start()

    client.loop_forever()

if __name__ == "__main__":
    main()

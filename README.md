# 🧩 Supla MQTT Autodiscovery  

**Autor:** MarHoi 

**Wersja:** xxx
**Platforma:** Home Assistant (Supervisor / Add-on)  
**Architektura:** aarch64  

---

## 📘 Opis

Dodatek **Supla MQTT Autodiscovery** automatycznie generuje i publikuje encje Home Assistant dla urządzeń pochodzących z **Supla MQTT Bridge**.  
Dzięki temu wszystkie Twoje urządzenia SUPLA (czujniki, przekaźniki, przełączniki itp.) pojawiają się automatycznie w Home Assistant — bez ręcznego konfigurowania.

Integracja wykorzystuje mechanizm **MQTT Discovery** (prefiks `homeassistant/`) i analizuje dane pochodzące z kanałów SUPLA (`supla/#`).

---

## ⚙️ Funkcje

✅ Automatyczne wykrywanie i rejestracja urządzeń SUPLA w Home Assistant  
✅ Obsługa czujników, przekaźników, przycisków, rolet, liczników energii i innych typów kanałów  
✅ Obsługa MQTT z uwierzytelnieniem  
✅ Możliwość filtrowania urządzeń (include/exclude)  
✅ Obsługa wielu prefixów MQTT (np. `supla` → `homeassistant`)  
✅ Integracja bezpośrednio z brokerem **core-mosquitto** lub zewnętrznym brokerem  
✅ Tryb TLS / bez TLS  
✅ Opcjonalny interwał publikacji (odświeżanie autodiscovery)  

---

## 🏗️ Instalacja

1. **Dodaj repozytorium** do Home Assistant: https://github.com/marcinh-boop/ha-addons.git

2. Przejdź do:  
**Ustawienia → Dodatki → Sklep z dodatkami → Repozytoria → Dodaj URL**

3. Po dodaniu znajdziesz dodatek:  
**"Supla MQTT Autodiscovery"**

4. Zainstaluj dodatek, a następnie przejdź do **Konfiguracji** i uzupełnij dane:

---

## ⚙️ Konfiguracja (`config.yaml`)

```yaml
mqtt_host: core-mosquitto     # Adres brokera MQTT
mqtt_port: 1883               # Port (1883 lub 8883 dla TLS)
mqtt_username: user           # Użytkownik MQTT
mqtt_password: pass           # Hasło MQTT
tls: false                    # Czy używać TLS (true/false)
ca_certs: ""                  # Ścieżka do certyfikatów (opcjonalnie)
supla_prefix: "supla"         # Prefiks danych SUPLA
discovery_prefix: "homeassistant"  # Prefiks autodiscovery
name_prefix: "Supla"          # Prefiks nazw urządzeń w HA
include_devices: []           # Lista ID urządzeń do uwzględnienia (opcjonalnie)
exclude_devices: []           # Lista ID urządzeń do pominięcia (opcjonalnie)
publish_interval: 0           # Interwał publikacji autodiscovery (0 = jednorazowo)

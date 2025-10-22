# 🧩 Supla MQTT Autodiscovery  
**Wersja:** xxx
**Autor:** MarHoi  
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

1. **Dodaj repozytorium** do Home Assistant:

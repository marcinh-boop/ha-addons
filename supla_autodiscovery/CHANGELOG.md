# Changelog

## 1.1.0-alpha (2025-10-22)
- Repozytorium publiczne (`marcinh-boop/ha-addons`) i poprawna „Lista zmian” w sklepie HA.
- Kompatybilność z `paho-mqtt` **1.x/2.x**:
  - warunkowy `CallbackAPIVersion` (brak błędu na paho 1.x),
  - `on_connect(..., properties=None)` zgodne z 2.x.
- Naprawa generatora UID dla faz: `p0`, `p1`, `p2`, `p3` (zamiast `p+phase/p0`).
- Naprawa logu discovery (złe odwołanie do `name`).
- Logger z **timestampami** + baner startowy z wersją paho; `flush=True`, by logi od razu trafiały do HA.
- Uporządkowane pliki dodatku; spójne `config.yaml` i `Dockerfile`.
- **Uwaga:** `publish_interval` jeszcze nie jest używany – funkcja do wdrożenia.

## 1.0.6-patched2 (2025-10-22)
- Poprawki paho 1.x/2.x, logi z timestampami, baner startowy.
- Fix UID (p0/p1..p3) i logu `name`.
- Przygotowanie CHANGELOG do wyświetlania w sklepie.

## 1.0.6-patched1 (2025-10-22)
- Pierwsza wersja patcha kompatybilności z paho 1.x/2.x (CallbackAPIVersion guard, `on_connect`).

## 1.0.6
- Drobne poprawki i aktualizacje (stan przed patchami paho).

## 1.0.3
- Pierwsze publiczne wydanie.

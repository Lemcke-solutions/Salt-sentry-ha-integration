# Salt Sentry — Home Assistant Integration

Integrates the **Salt Sentry** device into Home Assistant. Salt Sentry is an ultrasonic distance sensor (ESP8266/ESP32) that measures the salt level in a water softener tank and exposes it as a percentage via a local HTTP API.

## Features

- Salt level as a percentage (based on configured full/empty distances)
- Corrected and raw distance measurements
- Hardware revision sensor
- Automatic discovery via Zeroconf (mDNS)
- OTA firmware updates via Home Assistant's update entity
- Configurable scan interval and measurement correction
- Supports cm and inch

## Installation via HACS

1. Open HACS in Home Assistant
2. Go to **Integrations** → **Custom repositories**
3. Add `https://github.com/eriknl1982/salt_sentry_ha_integration` as an **Integration**
4. Search for **Salt Sentry** and install it
5. Restart Home Assistant

## Setup

The device is discovered automatically via Zeroconf when it is on the same network as Home Assistant. You can also add it manually via **Settings → Integrations → Add integration → Salt Sentry**.

During setup you will configure:
- **IP address** of the device
- **Unit** (cm or inch)
- **Water softener model** (to prefill the distances)
- **Distance when full** — sensor distance when the salt tank is full
- **Distance when empty** — sensor distance when the salt tank is empty
- **Scan interval** — how often HA polls the device (minutes)

A smaller distance means more salt (the sensor is mounted at the top of the tank).

## Entities

| Entity | Category | Description |
|--------|----------|-------------|
| Salt Level | — | Salt percentage (0–100%) |
| Salt Distance | — | Corrected distance measurement |
| Salt Distance raw | Diagnostic | Raw distance from the sensor, without correction |
| Hardware Revision | Diagnostic | Hardware revision of the device (A = ESP8266, B = ESP32) |
| Firmware | — | Update entity for OTA firmware updates |

## Supported water softeners

Preset distances are available for the following models. Choose **Other** to enter distances manually.

- Aqua Cell
- Other (manual input)

## Device API

The Salt Sentry device exposes a local HTTP API at `http://<device-ip>/status`. No cloud connection is required.

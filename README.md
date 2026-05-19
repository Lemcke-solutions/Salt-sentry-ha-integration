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

## Use cases

- Get a notification when your salt level drops below a threshold, so you never run out of salt unexpectedly.
- Track salt consumption trends over time using the history graph.
- Automate a reminder on the display of a smart home panel when a top-up is needed.
- Include salt level in a household maintenance dashboard.

## Installation via HACS

1. Open HACS in Home Assistant
2. Go to **Integrations** → **Custom repositories**
3. Add `https://github.com/Lemcke-solutions/Salt-sentry-ha-integration` as an **Integration**
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

## Removal

1. Go to **Settings → Integrations**
2. Find **Salt Sentry** and click the three-dot menu
3. Select **Delete**
4. Restart Home Assistant

If installed via HACS, also remove the integration there to clean up the files.

## Entities

| Entity | Category | Description |
|--------|----------|-------------|
| Salt Level | — | Salt percentage (0–100%) |
| Salt Distance | — | Corrected distance measurement |
| Salt Distance raw | Diagnostic | Raw distance from the sensor, without correction (disabled by default) |
| Hardware Revision | Diagnostic | Hardware revision of the device (A = ESP8266, B = ESP32) |
| Firmware | — | Update entity for OTA firmware updates |

## Data updates

Sensor data is fetched from the device on a configurable polling interval (default: 1 minute). The interval can be changed during setup or via **Options**. Firmware version availability is checked against GitHub Releases every 6 hours.

## Supported water softeners

Preset distances are available for the following models. Choose **Other** to enter distances manually.

| Model | Distance full | Distance empty |
|-------|--------------|----------------|
| Aqua Cell | 5 cm | 35 cm |
| Other | manual | manual |

## Automation examples

### Notify when salt level is low

```yaml
automation:
  - alias: "Salt level low notification"
    trigger:
      - platform: numeric_state
        entity_id: sensor.salt_sentry_salt_level
        below: 20
    action:
      - action: notify.notify
        data:
          title: "Salt Sentry"
          message: "Salt level is below 20%. Time to refill!"
```

### Weekly salt level report

```yaml
automation:
  - alias: "Weekly salt level report"
    trigger:
      - platform: time
        at: "09:00:00"
        weekday: mon
    action:
      - action: notify.notify
        data:
          title: "Salt Sentry"
          message: "Current salt level: {{ states('sensor.salt_sentry_salt_level') }}%"
```

## Known limitations

- Each Salt Sentry device requires its own integration entry; multiple devices need to be added separately.
- The salt percentage is calculated by linear interpolation between the configured full and empty distances. Non-linear tank shapes will reduce accuracy.
- The integration uses local polling; there is no push notification from the device.
- Firmware updates require the device to be reachable on the local network at the time of installation.

## Troubleshooting

**Device not found during setup**
- Confirm the IP address is correct and the device is powered on.
- Check that Home Assistant and the Salt Sentry device are on the same network or VLAN.

**Salt level seems incorrect**
- Go to **Options** and re-enter the full and empty distances after measuring with the device in place.
- Check the **Salt Distance raw** diagnostic entity to see what the sensor actually reports.
- Use the correction field in **Options** to fine-tune the reading.

**Firmware update fails**
- Confirm the device is reachable by opening `http://<device-ip>/status` in a browser.
- Check the **Firmware** entity for a valid latest version. If it shows unknown, the GitHub version check may have failed — restart HA to retry.

**Entity shows unavailable**
- The device could not be reached during the last poll. Check power and network connectivity. HA will automatically recover when the device is reachable again.

## Device API

The Salt Sentry device exposes a local HTTP API at `http://<device-ip>/status`. No cloud connection is required.

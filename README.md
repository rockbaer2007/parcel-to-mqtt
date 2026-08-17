# Parcel to MQTT

![Parcel to MQTT icon](./parcel_to_mqtt/icon.png)

Home Assistant app repository for publishing parcel tracking data through MQTT Discovery.

The current version uses direct DHL and Hermes parcel tracking with configured tracking numbers. Home Assistant notifications can be built with normal Home Assistant automations from the generated MQTT entities.

Adapted from and inspired by the original ioBroker adapter:
[TA2k/ioBroker.parcel](https://github.com/TA2k/ioBroker.parcel)

The shared parcel status model is inspired by the MIT licensed Home Assistant parcel integrations:
[ha-parcel-integrations](https://github.com/ha-parcel-integrations)

## Installation

[![Open your Home Assistant instance and add the Parcel to MQTT app repository](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Frockbaer2007%2Fparcel-to-mqtt)

1. Open Home Assistant.
2. Go to **Settings > Apps > App-Store**.
3. Open the three-dot menu and choose **Repositories**.
4. Add this repository URL:

   ```text
   https://github.com/rockbaer2007/parcel-to-mqtt
   ```

5. Install **Parcel to MQTT**.
6. Configure DHL and/or Hermes tracking numbers.
7. Start the app.

## Features

- Direct DHL parcel tracking.
- Direct Hermes Germany parcel tracking.
- Manual tracking numbers as comma-separated lists.
- GLS configuration is prepared, but GLS Germany polling is not active yet because it needs a guest bearer session.
- DPD and UPS are planned for a later step once a reliable direct, account or official API path is chosen.
- MQTT Discovery connection sensor.
- Parcel counters for all, registered, in transit, in delivery, pickup point, delivered, returning, exception and unknown.
- JSON sensor with all parcel data.
- Up to six parcel slot sensors with provider, status, last event and tracking number attributes.
- Home Assistant notifications through normal HA automations.

## Status

This is an early testable MVP. DHL and Hermes are active. GLS, DPD and UPS are the next provider targets.

## License

MIT

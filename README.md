# Parcel to MQTT

![Parcel to MQTT icon](./parcel_to_mqtt/icon.png)

Home Assistant app repository for publishing parcel tracking data through MQTT Discovery.

The first version uses the 17TRACK API and configured tracking numbers. Home Assistant notifications can be built with normal Home Assistant automations from the generated MQTT entities.

Adapted from and inspired by the original ioBroker adapter:
[TA2k/ioBroker.parcel](https://github.com/TA2k/ioBroker.parcel)

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
6. Configure the 17TRACK API key and tracking numbers.
7. Start the app.

## Features

- 17TRACK API lookup.
- Manual tracking numbers as comma-separated list.
- MQTT Discovery connection sensor.
- Parcel counters for all, in transit, in delivery, delivered, exception and unknown.
- JSON sensor with all parcel data.
- Up to six parcel slot sensors with provider, status, last event and tracking number attributes.
- Home Assistant notifications through normal HA automations.

## Status

This is an early testable MVP. More providers can be added later.

## License

MIT

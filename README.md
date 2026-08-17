# Parcel to MQTT

![Parcel to MQTT icon](./parcel_to_mqtt/icon.png)

Home Assistant app repository for publishing parcel tracking data through MQTT Discovery.

The current version uses DHL account tracking, optional manual DHL tracking numbers and Hermes parcel tracking. Home Assistant notifications can be built with normal Home Assistant automations from the generated MQTT entities.

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

- DHL account parcel list through the DHL browser login code.
- Optional direct DHL parcel tracking by manual tracking number.
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

## DHL account login

Open the DHL login URL, sign in, copy the failed `dhllogin://...` redirect from the browser developer console and paste it into `dhl_login_code`:

```text
https://login.dhl.de/af5f9bb6-27ad-4af4-9445-008e7a5cddb8/login/authorize?redirect_uri=dhllogin://de.deutschepost.dhl/login&state=eyJycyI6dHJ1ZSwicnYiOmZhbHNlLCJmaWQiOiJhcHAtbG9naW4tbWVoci1mb290ZXIiLCJoaWQiOiJhcHAtbG9naW4tbWVoci1oZWFkZXIiLCJycCI6ZmFsc2V9&client_id=83471082-5c13-4fce-8dcb-19d2a3fca413&response_type=code&scope=openid%20offline_access&claims=%7B%22id_token%22:%7B%22email%22:null,%22post_number%22:null,%22twofa%22:null,%22service_mask%22:null,%22deactivate_account%22:null,%22last_login%22:null,%22customer_type%22:null,%22display_name%22:null,%22data_confirmation_required%22:null%7D%7D&nonce=&login_hint=&prompt=login&ui_locales=de-DE&code_challenge=MAhrhXXZP-Owy-R7ruyB7Fn-Z8ODW6qxCoHg4uXELCw&code_challenge_method=S256
```

After the first successful login the app stores the refresh token in `/data/dhl_session.json` and reuses it on restart.

## License

MIT

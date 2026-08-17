# Parcel to MQTT

Home Assistant app for publishing parcel tracking data through MQTT Discovery.

Adapted from and inspired by the original ioBroker adapter:
[TA2k/ioBroker.parcel](https://github.com/TA2k/ioBroker.parcel)

The shared parcel status model is inspired by the MIT licensed Home Assistant parcel integrations:
[ha-parcel-integrations](https://github.com/ha-parcel-integrations)

## Entities

- `Parcel Verbindung`
- `Parcel letzte Aktualisierung`
- `Parcel Sendungen`
- `Parcel Gesamt`
- `Parcel Unterwegs`
- `Parcel In Zustellung`
- `Parcel Zugestellt`
- `Parcel Problem`
- `Parcel Unbekannt`
- `Parcel 01` through configured parcel slots

Each parcel slot exposes tracking number, carrier, status, last event, last event time and raw status as attributes.

## Configuration

```yaml
dhl_tracking_numbers: "00340434123456789012,00340434123456789013"
dhl_login_url: "https://login.dhl.de/..."
dhl_login_code: ""
hermes_tracking_numbers: "12345678901234"
gls_tracking_numbers: ""
gls_postal_code: ""
interval: 60
max_parcels: 6
log_response_details: false
```

`dhl_login_url` is a copy helper for the DHL browser login. Open it in Chrome, sign in to DHL, open the developer console with `F12`, copy the failed `dhllogin://...` redirect URL and paste it into `dhl_login_code`.
After the first successful login the app stores the refresh token in `/data/dhl_session.json` and reads the DHL account parcel list automatically.
`dhl_tracking_numbers` and `hermes_tracking_numbers` accept comma-separated lists.
GLS configuration is already present, but GLS Germany polling is not active yet because it needs a guest bearer session.
`log_response_details` writes masked provider requests and responses to the add-on log and `/data/provider_debug.log`. The file keeps at most 100 JSON lines.
Notifications should be created as Home Assistant automations using the generated entities.

## Provider roadmap

- DHL: active through `dhllogin://` browser login code plus optional manual tracking numbers.
- Amazon: planned with e-mail, password, optional OTP token and a cookie reset option.
- Hermes: currently active by manual tracking number; account login with app username and app password is planned.
- UPS: planned with app username and app password.
- GLS and DPD: planned after the stable login/session flow is mapped.

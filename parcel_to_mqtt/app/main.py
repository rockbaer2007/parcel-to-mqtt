from __future__ import annotations

import json
import logging
import os
import signal
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import paho.mqtt.client as mqtt
import requests


LOG = logging.getLogger("parcel_to_mqtt")
DEFAULT_BASE_TOPIC = "parcel"
DEFAULT_DISCOVERY_PREFIX = "homeassistant"
MAX_DEFAULT_PARCELS = 6


@dataclass(frozen=True)
class Options:
    dhl_tracking_numbers: list[str]
    interval: int
    max_parcels: int
    log_response_details: bool
    mqtt_host: str
    mqtt_port: int
    mqtt_username: str
    mqtt_password: str
    discovery_prefix: str
    base_topic: str
    retain: bool


@dataclass(frozen=True)
class Parcel:
    index: int
    tracking_number: str
    carrier: str
    status: str
    status_group: str
    last_event: str
    last_event_time: str
    destination: str
    raw: dict[str, Any]


class DhlClient:
    def __init__(self, options: Options) -> None:
        self.options = options
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "application/json",
            "content-type": "application/json",
            "accept-language": "de-de",
            "user-agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
        })

    def poll(self) -> list[Parcel]:
        if not self.options.dhl_tracking_numbers:
            return []
        try:
            response = self.session.get(
                "https://www.dhl.de/int-verfolgen/data/search",
                params={
                    "piececode": ",".join(self.options.dhl_tracking_numbers),
                    "noRedirect": "true",
                    "language": "de",
                    "cid": "app",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            if self.options.log_response_details:
                LOG.info("DHL tracking returned: %s", json.dumps(data, ensure_ascii=False, sort_keys=True)[:8000])
            shipments = data.get("sendungen", []) if isinstance(data, dict) else []
            if not isinstance(shipments, list):
                return []
            active_shipments = [
                shipment for shipment in shipments
                if value_at(shipment, ["sendungsinfo", "sendungsliste"]) != "ARCHIVIERT"
            ]
            parcels = [self.normalize_parcel(index, item) for index, item in enumerate(active_shipments, start=1)]
            return parcels[: self.options.max_parcels]
        except Exception as exc:
            LOG.warning("Could not fetch DHL parcel data: %s", exc)
            return []

    @staticmethod
    def normalize_parcel(index: int, item: dict[str, Any]) -> Parcel:
        status_text = first_text(
            value_at(item, ["sendungsdetails", "sendungsverlauf", "kurzStatus"]),
            value_at(item, ["sendungsdetails", "sendungsverlauf", "status"]),
            value_at(item, ["sendungsinfo", "status"]),
        )
        last_event, last_event_time = dhl_last_event(item)
        status_group = normalize_status_group(f"{status_text} {last_event}")
        return Parcel(
            index=index,
            tracking_number=str(item.get("id") or ""),
            carrier="DHL",
            status=status_text or human_status(status_group),
            status_group=status_group,
            last_event=last_event,
            last_event_time=last_event_time,
            destination=str(value_at(item, ["sendungsinfo", "zielland"]) or ""),
            raw=item,
        )


class MqttPublisher:
    def __init__(self, options: Options) -> None:
        self.options = options
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="parcel-to-mqtt")
        if options.mqtt_username:
            self.client.username_pw_set(options.mqtt_username, options.mqtt_password)
        self._published_discovery = False

    def connect(self) -> None:
        LOG.info("Using MQTT broker %s:%s as user '%s'", self.options.mqtt_host, self.options.mqtt_port, self.options.mqtt_username or "<empty>")
        self.client.on_connect = self._on_connect
        self.client.connect(self.options.mqtt_host, self.options.mqtt_port, keepalive=60)
        self.client.loop_start()

    def disconnect(self) -> None:
        self.client.loop_stop()
        self.client.disconnect()

    def publish_results(self, parcels: list[Parcel]) -> None:
        if not self._published_discovery:
            self.publish_discovery()
            self._published_discovery = True
        self._publish(f"{self.options.base_topic}/status", "online")
        self._publish(f"{self.options.base_topic}/last_update", datetime.now(timezone.utc).isoformat())
        summary = parcel_summary(parcels)
        self._publish_json(f"{self.options.base_topic}/all", [parcel_to_dict(parcel) for parcel in parcels])
        for key, value in summary.items():
            self._publish(f"{self.options.base_topic}/{key}", str(value))
        for index in range(1, self.options.max_parcels + 1):
            parcel = next((item for item in parcels if item.index == index), None)
            prefix = f"{self.options.base_topic}/parcels/{index:02d}"
            self._publish(f"{prefix}/status", parcel.status if parcel else "")
            self._publish_json(f"{prefix}/attributes", parcel_to_dict(parcel) if parcel else empty_parcel_attributes(index))
        LOG.info("Published %s parcel tracking entries", len(parcels))

    def publish_discovery(self) -> None:
        self._publish_config("binary_sensor", "connection", {
            "name": "Parcel Verbindung",
            "unique_id": "parcel_to_mqtt_connection",
            "state_topic": f"{self.options.base_topic}/status",
            "payload_on": "online",
            "payload_off": "offline",
            "device_class": "connectivity",
            "device": self._device(),
        })
        self._publish_config("sensor", "last_update", {
            "name": "Parcel letzte Aktualisierung",
            "unique_id": "parcel_to_mqtt_last_update",
            "state_topic": f"{self.options.base_topic}/last_update",
            "device_class": "timestamp",
            "device": self._device(),
        })
        self._publish_config("sensor", "all", {
            "name": "Parcel Sendungen",
            "unique_id": "parcel_to_mqtt_all",
            "state_topic": f"{self.options.base_topic}/total",
            "json_attributes_topic": f"{self.options.base_topic}/all",
            "icon": "mdi:package-variant-closed",
            "device": self._device(),
        })
        counters = {
            "total": ("Parcel Gesamt", "mdi:package-variant-closed"),
            "in_transit": ("Parcel Unterwegs", "mdi:truck-fast"),
            "out_for_delivery": ("Parcel In Zustellung", "mdi:truck-delivery"),
            "delivered": ("Parcel Zugestellt", "mdi:package-check"),
            "exception": ("Parcel Problem", "mdi:package-alert"),
            "unknown": ("Parcel Unbekannt", "mdi:package-question"),
        }
        for key, (name, icon) in counters.items():
            self._publish_config("sensor", key, {
                "name": name,
                "unique_id": f"parcel_to_mqtt_{key}",
                "state_topic": f"{self.options.base_topic}/{key}",
                "state_class": "measurement",
                "icon": icon,
                "device": self._device(),
            })
        for index in range(1, self.options.max_parcels + 1):
            self._publish_config("sensor", f"parcel_{index:02d}", {
                "name": f"Parcel {index:02d}",
                "unique_id": f"parcel_to_mqtt_parcel_{index:02d}",
                "state_topic": f"{self.options.base_topic}/parcels/{index:02d}/status",
                "json_attributes_topic": f"{self.options.base_topic}/parcels/{index:02d}/attributes",
                "icon": "mdi:package-variant-closed",
                "device": self._device(),
            })

    def _on_connect(self, client: mqtt.Client, userdata: Any, flags: Any, reason_code: Any, properties: Any) -> None:
        LOG.info("Connected to MQTT broker with result %s", reason_code)

    def _publish_config(self, component: str, object_id: str, payload: dict[str, Any]) -> None:
        self._publish_json(f"{self.options.discovery_prefix}/{component}/parcel_to_mqtt/{object_id}/config", payload, retain=True)

    def _publish_json(self, topic: str, payload: Any, retain: bool | None = None) -> None:
        self._publish(topic, json.dumps(payload, separators=(",", ":"), ensure_ascii=False), retain=retain)

    def _publish(self, topic: str, payload: str, retain: bool | None = None) -> None:
        self.client.publish(topic, payload, qos=0, retain=self.options.retain if retain is None else retain)

    @staticmethod
    def _device() -> dict[str, Any]:
        return {
            "identifiers": ["parcel_to_mqtt"],
            "name": "Parcel to MQTT",
            "manufacturer": "UGSo Software",
            "model": "Parcel Tracking App",
        }


def value_at(data: Any, path: list[str]) -> Any:
    current = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def first_text(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def dhl_last_event(item: dict[str, Any]) -> tuple[str, str]:
    history = value_at(item, ["sendungsdetails", "sendungsverlauf"])
    if isinstance(history, dict):
        events = history.get("events") or history.get("ereignisse") or history.get("eventsProgressbar")
        if isinstance(events, list) and events:
            latest = events[-1] if isinstance(events[-1], dict) else {}
            return (
                first_text(latest.get("status"), latest.get("text"), latest.get("description"), latest.get("ort")),
                first_text(latest.get("datum"), latest.get("zeit"), latest.get("timestamp"), latest.get("time")),
            )
    return (
        first_text(value_at(item, ["sendungsdetails", "sendungsverlauf", "status"]), value_at(item, ["sendungsinfo", "sendungsname"])),
        first_text(value_at(item, ["sendungsdetails", "sendungsverlauf", "datum"]), value_at(item, ["sendungsdetails", "sendungsverlauf", "zeit"])),
    )


def normalize_status_group(status: str) -> str:
    text = status.lower().replace("-", "_").replace(" ", "_")
    compact = text.replace("_", "")
    if ("wird" in text and "zugestellt" in text) or "in_zustellung" in text or "out_for_delivery" in text or "outfordelivery" in compact:
        return "out_for_delivery"
    if "delivered" in text or "zugestellt" in text or "ausgeliefert" in text:
        return "delivered"
    if "zustellung" in text or "pickup" in text:
        return "out_for_delivery"
    if "transit" in text or "transport" in text or "unterwegs" in text or "bearbeitung" in text or "info_received" in text or "inforeceived" in compact:
        return "in_transit"
    if "exception" in text or "expired" in text or "failed" in text or "problem" in text or "fehler" in text:
        return "exception"
    return "unknown"


def human_status(group: str) -> str:
    return {
        "delivered": "Zugestellt",
        "out_for_delivery": "In Zustellung",
        "in_transit": "Unterwegs",
        "exception": "Problem",
        "unknown": "Unbekannt",
    }.get(group, "Unbekannt")


def parcel_summary(parcels: list[Parcel]) -> dict[str, int]:
    summary = {
        "total": len(parcels),
        "in_transit": 0,
        "out_for_delivery": 0,
        "delivered": 0,
        "exception": 0,
        "unknown": 0,
    }
    for parcel in parcels:
        summary[parcel.status_group] = summary.get(parcel.status_group, 0) + 1
    return summary


def parcel_to_dict(parcel: Parcel) -> dict[str, Any]:
    return {
        "index": parcel.index,
        "tracking_number": parcel.tracking_number,
        "carrier": parcel.carrier,
        "status": parcel.status,
        "status_group": parcel.status_group,
        "last_event": parcel.last_event,
        "last_event_time": parcel.last_event_time,
        "destination": parcel.destination,
    }


def empty_parcel_attributes(index: int) -> dict[str, Any]:
    return {
        "index": index,
        "tracking_number": "",
        "carrier": "",
        "status": "",
        "status_group": "",
        "last_event": "",
        "last_event_time": "",
        "destination": "",
    }


def parse_dhl_numbers(value: Any) -> list[str]:
    if isinstance(value, list):
        items = value
    else:
        items = str(value or "").replace("\n", ",").split(",")
    result = []
    for item in items:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def load_options() -> Options:
    raw = {}
    options_file = os.environ.get("OPTIONS_FILE", "/data/options.json")
    if os.path.exists(options_file):
        with open(options_file, encoding="utf-8") as handle:
            raw = json.load(handle)
    mqtt = load_mqtt_service()
    return Options(
        dhl_tracking_numbers=parse_dhl_numbers(raw.get("dhl_tracking_numbers", "")),
        interval=max(30, int(raw.get("interval", 60))),
        max_parcels=max(1, min(20, int(raw.get("max_parcels", MAX_DEFAULT_PARCELS)))),
        log_response_details=bool(raw.get("log_response_details", False)),
        mqtt_host=str(raw.get("mqtt_host") or mqtt.get("host") or "core-mosquitto"),
        mqtt_port=int(raw.get("mqtt_port") or mqtt.get("port") or 1883),
        mqtt_username=str(raw.get("mqtt_username") or mqtt.get("username") or ""),
        mqtt_password=str(raw.get("mqtt_password") or mqtt.get("password") or ""),
        discovery_prefix=str(raw.get("discovery_prefix", DEFAULT_DISCOVERY_PREFIX)).strip("/"),
        base_topic=str(raw.get("base_topic", DEFAULT_BASE_TOPIC)).strip("/"),
        retain=bool(raw.get("retain", True)),
    )


def load_mqtt_service() -> dict[str, Any]:
    service_file = "/services/mqtt"
    if not os.path.exists(service_file):
        return {}
    try:
        with open(service_file, encoding="utf-8") as handle:
            data = json.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception as exc:
        LOG.warning("Could not read MQTT service file: %s", exc)
        return {}


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_args: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_args: stop_event.set())
    options = load_options()
    publisher = MqttPublisher(options)
    client = DhlClient(options)
    publisher.connect()
    try:
        while not stop_event.is_set():
            try:
                parcels = client.poll()
                publisher.publish_results(parcels)
            except Exception as exc:
                LOG.exception("Polling failed: %s", exc)
                publisher._publish(f"{options.base_topic}/status", "offline")
            stop_event.wait(options.interval * 60)
    finally:
        publisher._publish(f"{options.base_topic}/status", "offline")
        publisher.disconnect()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

# TODO: make retry connections to event hubs
# in case stream analytincs job is not running before
# starting the generator.

"""IoT telemetry event generator for local testing or Azure Event Hubs."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import random
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


ALERT_THRESHOLD = 45.0


@dataclass
class DeviceState:
	## Mutable device telemetry baseline used to generate smooth-ish readings

	temperature: float
	humidity: float


def utc_timestamp() -> str:
	## Return ISO-8601 UTC timestamp accepted by Stream Analytics
	return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def clamp(value: float, low: float, high: float) -> float:
	## Clamp a float to a closed interval
	return max(low, min(high, value))


def build_device_states(device_ids: Iterable[str], rng: random.Random) -> Dict[str, DeviceState]:
	## Initialize per-device baselines for more realistic telemetry
	return {
		device_id: DeviceState(
			temperature=rng.uniform(22.0, 33.0),
			humidity=rng.uniform(35.0, 65.0),
		)
		for device_id in device_ids
	}


def generate_event(
	device_id: str,
	states: Dict[str, DeviceState],
	rng: random.Random,
	spike_probability: float,
) -> dict:
	## Generate one telemetry event matching the Stream Analytics input schema
	state = states[device_id]

	# Random walk keeps values changing gradually.
	state.temperature = clamp(state.temperature + rng.uniform(-0.8, 0.8), 18.0, 42.0)
	state.humidity = clamp(state.humidity + rng.uniform(-2.0, 2.0), 20.0, 90.0)

	temperature = state.temperature
	if rng.random() < spike_probability:
		# Inject occasional spikes to trigger alert stream (temperature > 45.0).
		temperature = rng.uniform(46.0, 55.0)

	status = "alert" if temperature > ALERT_THRESHOLD else "ok"

	return {
		"device_id": device_id,
		"temperature": round(temperature, 2),
		"humidity": round(state.humidity, 2),
		"status": status,
		"timestamp": utc_timestamp(),
	}


def create_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Generate IoT telemetry events for local tests or Azure Event Hubs."
	)
	parser.add_argument(
		"--mode",
		choices=["stdout", "file", "eventhub"],
		default="stdout",
		help="Output mode. Default: stdout.",
	)
	parser.add_argument(
		"--interval",
		type=float,
		default=1.0,
		help="Seconds between events. Default: 1.0.",
	)
	parser.add_argument(
		"--count",
		type=int,
		default=0,
		help="Number of events to emit. 0 means run forever. Default: 0.",
	)
	parser.add_argument(
		"--devices",
		type=int,
		default=5,
		help="Number of simulated devices. Default: 5.",
	)
	parser.add_argument(
		"--device-prefix",
		default="device",
		help="Prefix for generated device IDs. Default: device.",
	)
	parser.add_argument(
		"--spike-probability",
		type=float,
		default=0.05,
		help="Probability of high-temperature spike. Default: 0.05.",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=None,
		help="Random seed for repeatable output.",
	)
	parser.add_argument(
		"--output-file",
		default="",
		help="Path to output file when --mode file is selected.",
	)
	parser.add_argument(
		"--pretty",
		action="store_true",
		help="Pretty-print JSON in stdout mode.",
	)
	parser.add_argument(
		"--eventhub-connection-string",
		default=os.getenv("EVENTHUB_CONNECTION_STRING", ""),
		help="Event Hub namespace or entity connection string.",
	)
	parser.add_argument(
		"--eventhub-name",
		default=os.getenv("EVENTHUB_NAME", "telemetry"),
		help="Event Hub name (required with namespace-level connection string).",
	)
	return parser


def validate_args(args: argparse.Namespace) -> None:
	if args.devices <= 0:
		raise ValueError("--devices must be > 0")
	if args.interval <= 0:
		raise ValueError("--interval must be > 0")
	if args.count < 0:
		raise ValueError("--count must be >= 0")
	if not 0.0 <= args.spike_probability <= 1.0:
		raise ValueError("--spike-probability must be between 0.0 and 1.0")
	if args.mode == "file" and not args.output_file:
		raise ValueError("--output-file is required when --mode file")
	if args.mode == "eventhub" and not args.eventhub_connection_string:
		raise ValueError(
			"--eventhub-connection-string is required when --mode eventhub"
		)


def emit_stdout(event: dict, pretty: bool) -> None:
	if pretty:
		print(json.dumps(event, indent=2), flush=True)
	else:
		print(json.dumps(event, separators=(",", ":")), flush=True)


def emit_file(file_path: Path, event: dict) -> None:
	with file_path.open("a", encoding="utf-8") as handle:
		handle.write(json.dumps(event, separators=(",", ":")))
		handle.write("\n")


def create_eventhub_client(connection_string: str, eventhub_name: str) -> Any:
	try:
		eventhub_module = importlib.import_module("azure.eventhub")
	except ImportError as exc:
		raise RuntimeError(
			"Missing dependency 'azure-eventhub'"
		) from exc

	producer_client_class = getattr(eventhub_module, "EventHubProducerClient", None)
	if producer_client_class is None:
		raise RuntimeError("Could not load EventHubProducerClient from azure.eventhub")

	return producer_client_class.from_connection_string(
		conn_str=connection_string,
		eventhub_name=eventhub_name,
	)


def get_event_data_class() -> Any:
	try:
		eventhub_module = importlib.import_module("azure.eventhub")
	except ImportError as exc:
		raise RuntimeError(
			"Missing dependency 'azure-eventhub'"
		) from exc

	event_data_class = getattr(eventhub_module, "EventData", None)
	if event_data_class is None:
		raise RuntimeError("Could not load EventData from azure.eventhub")

	return event_data_class


def run_eventhub_mode(args: argparse.Namespace, events: Iterable[dict]) -> int:
	producer = create_eventhub_client(
		connection_string=args.eventhub_connection_string,
		eventhub_name=args.eventhub_name,
	)
	event_data = get_event_data_class()
	batch = producer.create_batch()
	events_sent = 0

	try:
		for event in events:
			payload = json.dumps(event, separators=(",", ":"))
			item = event_data(payload)
			try:
				batch.add(item)
			except ValueError:
				producer.send_batch(batch)
				batch = producer.create_batch()
				batch.add(item)
			events_sent += 1
	finally:
		if len(batch) > 0:
			producer.send_batch(batch)
		producer.close()

	return events_sent


def run(args: argparse.Namespace) -> int:
	rng = random.Random(args.seed)
	device_ids = [f"{args.device_prefix}-{index:03d}" for index in range(1, args.devices + 1)]
	states = build_device_states(device_ids, rng)

	max_events: Optional[int] = args.count if args.count > 0 else None
	file_path = Path(args.output_file) if args.output_file else None
	events_sent = 0

	try:
		def event_stream() -> Iterable[dict]:
			events_generated = 0
			while max_events is None or events_generated < max_events:
				device_id = rng.choice(device_ids)
				event = generate_event(device_id, states, rng, args.spike_probability)
				events_generated += 1
				yield event
				if max_events is None or events_generated < max_events:
					time.sleep(args.interval)

		if args.mode == "eventhub":
			events_sent = run_eventhub_mode(args, event_stream())
		else:
			for event in event_stream():
				if args.mode == "stdout":
					emit_stdout(event, pretty=args.pretty)
				else:
					if file_path is None:
						raise RuntimeError("Output file path is required in file mode")
					emit_file(file_path, event)
				events_sent += 1
	except KeyboardInterrupt:
		print("\nInterrupted by user.", file=sys.stderr)

	print(f"Events emitted: {events_sent}", file=sys.stderr)
	return 0


def main() -> int:
	parser = create_parser()
	args = parser.parse_args()

	try:
		validate_args(args)
	except ValueError as exc:
		parser.error(str(exc))

	return run(args)


if __name__ == "__main__":
	raise SystemExit(main())





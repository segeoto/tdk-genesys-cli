"""Core command helpers and active-target session management."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import TypeVar

from gen.config import FAULT_BITS, SESSION_DIR, SESSION_FILE
from gen.driver import GenesysDriver, validate_ip

T = TypeVar("T")

NO_ACTIVE_TARGET_MESSAGE = "No active target. Use: gen connect <ip>"


def save_target_ip(ip: str) -> None:
    """Persist the active target IP address."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    SESSION_FILE.write_text(json.dumps({"ip": ip}, indent=2), encoding="utf-8")


def load_target_ip() -> str:
    """Load the active target IP address."""
    if not SESSION_FILE.exists():
        raise RuntimeError(NO_ACTIVE_TARGET_MESSAGE)

    try:
        raw_data = SESSION_FILE.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"Unable to read session file: {exc}") from exc

    if not raw_data.strip():
        raise RuntimeError(
            f"Empty session file: {SESSION_FILE}. "
            "Run: gen disconnect or remove the file, then reconnect."
        )

    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"Invalid session file: {SESSION_FILE}. "
            "Run: gen disconnect or remove the file, then reconnect."
        ) from exc

    ip = data.get("ip", "").strip()
    if not ip:
        raise RuntimeError(NO_ACTIVE_TARGET_MESSAGE)

    try:
        return validate_ip(ip)
    except ValueError as exc:
        raise RuntimeError(
            f"Invalid target IP in session file: {ip}. "
            "Run: gen disconnect or remove the file, then reconnect."
        ) from exc


def clear_target_ip() -> None:
    """Clear the persisted active target IP address."""
    if not SESSION_FILE.exists():
        return

    try:
        SESSION_FILE.unlink()
    except OSError as exc:
        raise RuntimeError(f"Unable to remove session file: {exc}") from exc


def echo_error(message: str) -> None:
    """Print an error message to stderr."""
    print(f"Error: {message}", file=sys.stderr)


def decode_faults(value: int) -> list[str]:
    """Decode active faults from the status register."""
    active_faults: list[str] = []

    for bit_index, label in FAULT_BITS.items():
        if value & (1 << bit_index):
            active_faults.append(label)

    return active_faults


def _exit_with_error(exc: Exception, code: int = 1) -> None:
    """Print a CLI error and terminate."""
    echo_error(str(exc))
    raise SystemExit(code) from exc


def run_with_active_target(action: Callable[[GenesysDriver], T]) -> T:
    """Run an action against the currently selected target."""
    try:
        ip = load_target_ip()
        with GenesysDriver(ip) as driver:
            return action(driver)
    except Exception as exc:
        _exit_with_error(exc)


def connect_command(ip: str) -> None:
    """Validate, probe, and save the active target IP."""
    try:
        validated_ip = validate_ip(ip)
    except ValueError as exc:
        _exit_with_error(exc, code=2)

    try:
        with GenesysDriver(validated_ip) as driver:
            idn = driver.ping()
    except Exception as exc:
        _exit_with_error(exc)

    save_target_ip(validated_ip)
    print(f"Active target set to {validated_ip}")
    print(f"Instrument: {idn}")


def disconnect_command() -> None:
    """Apply safe shutdown and clear the active target."""
    try:
        ip = load_target_ip()
        with GenesysDriver(ip) as driver:
            driver.apply_safe_shutdown()
        clear_target_ip()
    except Exception as exc:
        _exit_with_error(exc)

    print(f"Disconnected from {ip}")
    print("Safe shutdown applied: output off, voltage set to 0 V, current set to 0 A.")


def ping_command() -> None:
    """Check communication with the active target."""
    idn = run_with_active_target(lambda driver: driver.ping())
    print(f"Ping OK: {idn}")


def info_command() -> None:
    """Read and display instrument information."""
    data = run_with_active_target(lambda driver: driver.read_info())
    print(f"IP          : {data.ip}")
    print(f"Hostname    : {data.hostname}")
    print(f"SCPI        : {data.scpi_version}")
    print(f"IDN         : {data.idn}")


def faults_command() -> None:
    """Read and display active faults."""
    value = run_with_active_target(lambda driver: driver.read_fault_register())
    active_faults = decode_faults(value)

    print(f"Fault register: {value}")
    if not active_faults:
        print("No active faults")
        return

    print("Active faults:")
    for fault in active_faults:
        print(f"- {fault}")

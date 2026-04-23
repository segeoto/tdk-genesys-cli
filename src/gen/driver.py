"""Low-level PyVISA/SCPI driver for a Genesys instrument."""

from __future__ import annotations

import ipaddress
import time
from dataclasses import dataclass
from typing import Any

import pyvisa

from gen.config import (
    CMD_QUERY_FAULTS,
    CMD_QUERY_FOLDBACK,
    CMD_QUERY_HOSTNAME,
    CMD_QUERY_IDN,
    CMD_QUERY_MEASURED_CURRENT,
    CMD_QUERY_MEASURED_VOLTAGE,
    CMD_QUERY_OUTPUT,
    CMD_QUERY_OVP,
    CMD_QUERY_PROGRAMMED_CURRENT,
    CMD_QUERY_PROGRAMMED_VOLTAGE,
    CMD_QUERY_SCPI_VERSION,
    CMD_QUERY_UVL,
    CMD_SET_BLINK,
    CMD_SET_CURRENT,
    CMD_SET_FOLDBACK,
    CMD_SET_OUTPUT_OFF,
    CMD_SET_OUTPUT_ON,
    CMD_SET_OVP,
    CMD_SET_REMOTE,
    CMD_SET_UVL,
    CMD_SET_VOLTAGE,
    I_MAX,
    VISA_TIMEOUT_MS,
    V_MAX,
)


@dataclass
class StatusSnapshot:
    """Snapshot of output state and measurements."""

    ip: str
    output_on: bool | None
    programmed_voltage: float
    programmed_current: float
    measured_voltage: float
    measured_current: float

    @property
    def power(self) -> float:
        """Return measured output power in watts."""
        return self.measured_voltage * self.measured_current


@dataclass
class InstrumentInfo:
    """Basic identification and interface information."""

    ip: str
    idn: str
    scpi_version: str
    hostname: str


def validate_ip(ip: str) -> str:
    """Validate an IPv4 or IPv6 address string."""
    candidate = ip.strip()

    if not candidate:
        raise ValueError("Invalid IP address")

    try:
        ipaddress.ip_address(candidate)
    except ValueError as exc:
        raise ValueError(f"Invalid IP address: {ip}") from exc

    return candidate


def parse_on_off(value: str) -> bool | None:
    """Parse common ON/OFF representations."""
    normalized = value.strip().upper()

    if normalized in {"1", "ON"}:
        return True
    if normalized in {"0", "OFF"}:
        return False
    return None


class GenesysDriver:
    """Low-level PyVISA/SCPI driver for a single Genesys instrument."""

    def __init__(self, ip: str) -> None:
        """Initialize the driver for a validated target IP."""
        self.ip = validate_ip(ip)
        self.resource_manager = pyvisa.ResourceManager("@py")
        self.instrument: Any | None = None

    def open(self) -> None:
        """Open the VISA resource if needed."""
        if self.instrument is not None:
            return

        self.instrument = self.resource_manager.open_resource(
            f"TCPIP0::{self.ip}::inst0::INSTR",
            write_termination="\n",
            timeout=VISA_TIMEOUT_MS,
        )

    def close(self) -> None:
        """Close the VISA resource if it is open."""
        if self.instrument is None:
            return

        try:
            self.instrument.close()
        finally:
            self.instrument = None

    def __enter__(self) -> GenesysDriver:
        """Open the resource when entering a context manager."""
        self.open()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Close the resource when leaving a context manager."""
        self.close()

    def _require_connection(self) -> None:
        """Raise if the instrument is not connected."""
        if self.instrument is None:
            raise RuntimeError("Instrument not connected")

    def write(self, command: str) -> None:
        """Send a SCPI command."""
        self._require_connection()
        self.instrument.write(command)

    def query_text(self, command: str) -> str:
        """Send a SCPI query and return stripped text."""
        self._require_connection()
        return self.instrument.query(command).strip()

    def query_float(self, command: str) -> float:
        """Send a SCPI query and parse the response as a float."""
        return float(self.query_text(command))

    def ensure_remote(self) -> None:
        """Switch the instrument to remote mode."""
        self.write(CMD_SET_REMOTE)
        time.sleep(0.10)

    def apply_safe_shutdown(self) -> None:
        """Apply the validated safe shutdown sequence."""
        try:
            self.ensure_remote()
        except Exception:
            pass

        try:
            self.write(CMD_SET_OUTPUT_OFF)
        except Exception:
            pass
        time.sleep(0.05)

        try:
            self.write(CMD_SET_VOLTAGE.format(value=0.0))
        except Exception:
            pass
        time.sleep(0.05)

        try:
            self.write(CMD_SET_CURRENT.format(value=0.0))
        except Exception:
            pass
        time.sleep(0.10)

    def ping(self) -> str:
        """Read the instrument identification string."""
        return self.query_text(CMD_QUERY_IDN)

    def read_status(self) -> StatusSnapshot:
        """Read programmed and measured output status."""
        programmed_voltage = self.query_float(CMD_QUERY_PROGRAMMED_VOLTAGE)
        programmed_current = self.query_float(CMD_QUERY_PROGRAMMED_CURRENT)
        measured_voltage = self.query_float(CMD_QUERY_MEASURED_VOLTAGE)
        measured_current = self.query_float(CMD_QUERY_MEASURED_CURRENT)
        output_on = parse_on_off(self.query_text(CMD_QUERY_OUTPUT))

        return StatusSnapshot(
            ip=self.ip,
            output_on=output_on,
            programmed_voltage=programmed_voltage,
            programmed_current=programmed_current,
            measured_voltage=measured_voltage,
            measured_current=measured_current,
        )

    def set_voltage_current(self, voltage: float, current: float) -> None:
        """Set both voltage and current setpoints."""
        if not 0.0 <= voltage <= V_MAX:
            raise ValueError(f"Voltage must be between 0 and {V_MAX:.1f} V")
        if not 0.0 <= current <= I_MAX:
            raise ValueError(f"Current must be between 0 and {I_MAX:.1f} A")

        self.ensure_remote()
        self.write(CMD_SET_VOLTAGE.format(value=voltage))
        self.write(CMD_SET_CURRENT.format(value=current))
        time.sleep(0.10)

    def set_output(self, state: bool) -> None:
        """Turn the output on or off."""
        self.ensure_remote()
        self.write(CMD_SET_OUTPUT_ON if state else CMD_SET_OUTPUT_OFF)
        time.sleep(0.20)

    def read_info(self) -> InstrumentInfo:
        """Read basic instrument identity and interface information."""
        return InstrumentInfo(
            ip=self.ip,
            idn=self.query_text(CMD_QUERY_IDN),
            scpi_version=self.query_text(CMD_QUERY_SCPI_VERSION),
            hostname=self.query_text(CMD_QUERY_HOSTNAME),
        )

    def read_fault_register(self) -> int:
        """Read the active fault register."""
        return int(self.query_text(CMD_QUERY_FAULTS))

    def set_blink(self, state: bool) -> None:
        """Enable or disable the LAN identify blink."""
        self.ensure_remote()
        self.write(CMD_SET_BLINK.format(state="ON" if state else "OFF"))

    def set_foldback(self, state: bool) -> None:
        """Enable or disable foldback protection."""
        self.ensure_remote()
        self.write(CMD_SET_FOLDBACK.format(state="ON" if state else "OFF"))
        time.sleep(0.10)

    def read_foldback(self) -> bool | None:
        """Read the foldback protection state."""
        return parse_on_off(self.query_text(CMD_QUERY_FOLDBACK))

    def set_ovp(self, value: float) -> None:
        """Set the overvoltage protection level."""
        if value < 0.0:
            raise ValueError("OVP must be greater than or equal to 0 V")

        self.ensure_remote()
        self.write(CMD_SET_OVP.format(value=value))
        time.sleep(0.10)

    def read_ovp(self) -> float:
        """Read the overvoltage protection level."""
        return self.query_float(CMD_QUERY_OVP)

    def set_uvl(self, value: float) -> None:
        """Set the undervoltage limit."""
        if value < 0.0:
            raise ValueError("UVL must be greater than or equal to 0 V")

        self.ensure_remote()
        self.write(CMD_SET_UVL.format(value=value))
        time.sleep(0.10)

    def read_uvl(self) -> float:
        """Read the undervoltage limit."""
        return self.query_float(CMD_QUERY_UVL)

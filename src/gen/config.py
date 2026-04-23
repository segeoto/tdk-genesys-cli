"""Configuration constants for the Genesys CLI."""

from __future__ import annotations

from pathlib import Path

APP_HELP = "TDK-Lambda Genesys CLI using PyVISA/SCPI."

V_MAX = 40.0
I_MAX = 38.0
VISA_TIMEOUT_MS = 1000

SESSION_DIR = Path.home() / ".gen"
SESSION_FILE = SESSION_DIR / "session.json"

CMD_SET_REMOTE = "SYST:SET REM"
CMD_SET_OUTPUT_ON = "OUTP:STAT ON"
CMD_SET_OUTPUT_OFF = "OUTP:STAT OFF"
CMD_QUERY_OUTPUT = "OUTP:STAT?"
CMD_SET_VOLTAGE = "SOUR:VOLT {value:.3f}"
CMD_SET_CURRENT = "SOUR:CURR:LEV:IMM:AMPL {value:.3f}"
CMD_QUERY_MEASURED_VOLTAGE = "MEAS:VOLT?"
CMD_QUERY_MEASURED_CURRENT = "MEAS:CURR?"
CMD_QUERY_PROGRAMMED_VOLTAGE = "SOUR:VOLT?"
CMD_QUERY_PROGRAMMED_CURRENT = "SOUR:CURR?"
CMD_QUERY_IDN = "*IDN?"
CMD_QUERY_SCPI_VERSION = "SYST:VERS?"
CMD_QUERY_HOSTNAME = "SYST:COMM:LAN:HOST?"
CMD_QUERY_FAULTS = "STAT:QUES:COND?"

CMD_SET_BLINK = "SYST:COMM:LAN:IDLED {state}"

CMD_SET_FOLDBACK = ":CURR:PROT:STAT {state}"
CMD_QUERY_FOLDBACK = ":CURR:PROT:STAT?"

CMD_SET_OVP = ":VOLT:PROT:LEV {value:.3f}"
CMD_QUERY_OVP = ":VOLT:PROT:LEV?"

CMD_SET_UVL = ":VOLT:LIM:LOW {value:.3f}"
CMD_QUERY_UVL = ":VOLT:LIM:LOW?"

FAULT_BITS = {
    1: "AC fault",
    2: "OTP over-temperature",
    3: "FLD foldback",
    4: "OVP over-voltage",
    5: "SO shut-off",
    6: "OFF output off",
    7: "ENA enable fault",
    8: "INPO internal input overflow",
    9: "INTO internal overflow",
    10: "ITMO internal timeout",
    11: "ICOM internal communication error",
}

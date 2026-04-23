# TDK-Lambda Genesys CLI

Command-line interface for controlling TDK-Lambda Genesys power supplies over LAN using SCPI and PyVISA.

The current CLI implementation is based on Python `argparse` for a small dependency footprint and straightforward maintenance.

The project focuses on a small, explicit command set, a stored target IP, and a conservative shutdown sequence for critical operations.

## Requirements

- Python 3.10 or newer.
- A working Python environment with `pyvisa` and `pyvisa-py`.
- A reachable TDK-Lambda Genesys power supply over LAN.
- SCPI access enabled on the instrument.

## Installation

Clone the repository, then run `pip install -e .` from the repository root.

This installs the `gen` command from the local source tree.

Run `pip install -e .` again after changes to package metadata or configuration files.

## Project Architecture

- `cli.py`: `argparse`-based command-line parsing and help output.
- `config.py`: constants, limits, SCPI commands, and local session paths.
- `core.py`: active target management and core commands.
- `controls.py`: output, protection, and identification control commands.
- `driver.py`: low-level PyVISA / SCPI driver.
- `__init__.py`: package metadata.

## Operating Model

The CLI uses a non-persistent communication model.

The operating sequence is as follows:

- `gen connect <ip>` stores the active target IP locally.
- Each subsequent command opens a new connection to the instrument.
- The requested operation is executed.
- The connection is then closed.

This design avoids maintaining a long-lived LAN session while preserving convenient access to the active target.

### Local Session

After a successful `gen connect <ip>`, the active target is stored in a local session file under the user home directory.

- Typical location on Linux and macOS: `~/.gen/session.json`
- Typical location on Windows: `C:\Users\<user>\.gen\session.json`

This file is used only to remember the active instrument target between commands.

## Model-specific Limits

The default voltage and current limits in `config.py` are currently set for the hardware used during development and validation.

If you use a different TDK-Lambda Genesys model, update `V_MAX` and `I_MAX` in `src/gen/config.py` to match the maximum voltage and current ratings of your power supply. This keeps local range validation consistent with the instrument.

At present, these limits are not detected automatically from the instrument model.

## Usage

```text
gen [-h] [-v] COMMAND ...
```

The CLI is organized into two command groups: Core and Controls.

Core commands run directly. `connect` requires an IP.

Control commands require a subcommand. Use `gen CONTROL --help` for available subcommands and usage details.

### Core

| Command | Description |
| --- | --- |
| `connect` | Validate the target IP, query the instrument, and save it as the active target. |
| `disconnect` | Apply the safe shutdown sequence and forget the active target. |
| `ping` | Check communication with the active target. |
| `info` | Read instrument information. |
| `faults` | Read and decode active faults. |

### Controls

| Command | Description |
| --- | --- |
| `output` | Read output status, apply voltage and current setpoints, switch output on or off, or apply the safe shutdown sequence. |
| `foldback` | Read or change the foldback protection state. |
| `ovp` | Read or set the overvoltage protection level. |
| `uvl` | Read or set the undervoltage limit. |
| `blink` | Enable or disable front and rear LED blinking for instrument identification (Blink Identify). |

### Safe Shutdown Behavior

A safe shutdown sequence is applied by `gen disconnect` and `gen output reset`.

The sequence is executed in the following order:

1. Turn output off.
2. Set voltage to 0 V.
3. Set current to 0 A.

This sequence is an intentional part of the CLI safety design.

## Notes on Instrument Behavior

This CLI writes settings through the instrument LAN / SCPI interface and then reports the state returned by the instrument after the write attempt.

Some settings may remain unchanged if the requested value is not accepted by the instrument in its current operating state. This can affect protection-related settings such as OVP and UVL.

UVL and OVP depend on the current programmed voltage. In practice, set the output voltage first, then adjust UVL and OVP while maintaining the margin recommended by the manufacturer.

For model-specific behavior and operating constraints, refer to the TDK-Lambda Genesys LAN Interface Manual and the user manual for your power supply model.

## Troubleshooting Network Connection Issues

If `gen connect <ip>` fails with an error such as `Error: [Errno 111] Connection refused`, this does not necessarily mean that the IP address is wrong or that the CLI is faulty.

In this case, the instrument may still respond to ICMP ping while the LAN / VXI-11 instrument service refuses the connection.

### Recommended Checks

1. Verify basic network reachability with `ping <ip>`.
2. Retry the CLI connection with `gen connect <ip>`.
3. If the instrument responds to `ping` but the same error persists, check the LAN path and any intermediate network equipment.
4. If needed, restart the network path or power-cycle the instrument.

A successful `ping` only confirms IP reachability. It does not guarantee that the instrument SCPI / VXI-11 service is available.

In practice, this error can be caused by a temporary network or transport issue even when the power supply is reachable on the network.

## License

This project is licensed under the MIT License.
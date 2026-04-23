"""Control command implementations for output and protections."""

from __future__ import annotations

from gen.core import run_with_active_target
from gen.driver import GenesysDriver, StatusSnapshot


def format_output_state(value: bool | None) -> str:
    """Format an ON/OFF/UNKNOWN state string."""
    if value is True:
        return "ON"
    if value is False:
        return "OFF"
    return "UNKNOWN"


def format_status(snapshot: StatusSnapshot) -> str:
    """Format an output status snapshot for display."""
    return (
        f"IP        : {snapshot.ip}\n"
        f"Output    : {format_output_state(snapshot.output_on)}\n"
        f"Measured V: {snapshot.measured_voltage:.3f} V\n"
        f"Measured A: {snapshot.measured_current:.3f} A\n"
        f"Power     : {snapshot.power:.3f} W\n"
        f"Set V     : {snapshot.programmed_voltage:.3f} V\n"
        f"Set A     : {snapshot.programmed_current:.3f} A"
    )


def output_status_command() -> None:
    """Read and display output status."""
    snapshot = run_with_active_target(lambda driver: driver.read_status())
    print(format_status(snapshot))


def output_set_command(voltage: float, current: float) -> None:
    """Apply output setpoints and display the resulting status."""

    def action(driver: GenesysDriver) -> StatusSnapshot:
        driver.set_voltage_current(voltage, current)
        return driver.read_status()

    snapshot = run_with_active_target(action)
    print("Setpoints applied.")
    print(format_status(snapshot))


def output_on_command() -> None:
    """Turn the output on and display the resulting status."""

    def action(driver: GenesysDriver) -> StatusSnapshot:
        driver.set_output(True)
        return driver.read_status()

    snapshot = run_with_active_target(action)
    print("Output ON")
    print(format_status(snapshot))


def output_off_command() -> None:
    """Turn the output off and display the resulting status."""

    def action(driver: GenesysDriver) -> StatusSnapshot:
        driver.set_output(False)
        return driver.read_status()

    snapshot = run_with_active_target(action)
    print("Output OFF")
    print(format_status(snapshot))


def output_reset_command() -> None:
    """Apply safe shutdown and display the resulting status."""

    def action(driver: GenesysDriver) -> StatusSnapshot:
        driver.apply_safe_shutdown()
        return driver.read_status()

    snapshot = run_with_active_target(action)
    print("Safety sequence applied.")
    print(format_status(snapshot))


def blink_on_command() -> None:
    """Enable blink identify mode."""
    run_with_active_target(lambda driver: driver.set_blink(True))
    print("Blink ON")


def blink_off_command() -> None:
    """Disable blink identify mode."""
    run_with_active_target(lambda driver: driver.set_blink(False))
    print("Blink OFF")


def foldback_status_command() -> None:
    """Read and display the foldback state."""
    state = run_with_active_target(lambda driver: driver.read_foldback())
    print(f"Foldback protection: {format_output_state(state)}")


def foldback_on_command() -> None:
    """Enable foldback protection and display the resulting state."""

    def action(driver: GenesysDriver) -> bool | None:
        driver.set_foldback(True)
        return driver.read_foldback()

    state = run_with_active_target(action)
    print(f"Foldback protection: {format_output_state(state)}")


def foldback_off_command() -> None:
    """Disable foldback protection and display the resulting state."""

    def action(driver: GenesysDriver) -> bool | None:
        driver.set_foldback(False)
        return driver.read_foldback()

    state = run_with_active_target(action)
    print(f"Foldback protection: {format_output_state(state)}")


def ovp_status_command() -> None:
    """Read and display the OVP setting."""
    value = run_with_active_target(lambda driver: driver.read_ovp())
    print(f"OVP: {value:.3f} V")


def ovp_set_command(value: float) -> None:
    """Set OVP and display the resulting value."""

    def action(driver: GenesysDriver) -> float:
        driver.set_ovp(value)
        return driver.read_ovp()

    ovp_value = run_with_active_target(action)
    print(f"OVP set to {ovp_value:.3f} V")


def uvl_status_command() -> None:
    """Read and display the UVL setting."""
    value = run_with_active_target(lambda driver: driver.read_uvl())
    print(f"UVL: {value:.3f} V")


def uvl_set_command(value: float) -> None:
    """Set UVL and display the resulting value."""

    def action(driver: GenesysDriver) -> float:
        driver.set_uvl(value)
        return driver.read_uvl()

    uvl_value = run_with_active_target(action)
    print(f"UVL set to {uvl_value:.3f} V")

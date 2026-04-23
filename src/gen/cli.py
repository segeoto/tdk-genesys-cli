"""Argparse CLI entry point for the Genesys command-line interface."""

from __future__ import annotations

import argparse
import re
from collections.abc import Callable, Sequence
from typing import Any

from gen import __release_date__, __version__
from gen.config import APP_HELP

AnySubparsers = Any


def _format_root_help() -> str:
    """Return the custom root help text."""
    return "\n".join(
        [
            "usage: gen [-h] [-v] COMMAND ...",
            "",
            APP_HELP,
            "",
            "The CLI is organized into two command groups: Core and Controls.",
            "",
            "Run Core commands directly. 'connect' requires an IP.",
            "Control commands require a subcommand. Use 'gen CONTROL --help' for available subcommands and usage details.",
            "",
            "Options:",
            "  -h, --help     Show this help message and exit",
            "  -v, --version  Show the program's version number and exit",
            "",
            "Core:",
            "  connect      Select and validate the active target IP",
            "  disconnect   Apply safe shutdown and forget target",
            "  ping         Check communication with active target",
            "  info         Read instrument information",
            "  faults       Read and decode active faults",
            "",
            "Controls:",
            "  output       Output control and setpoints",
            "  foldback     Foldback protection control",
            "  ovp          Overvoltage protection control",
            "  uvl          Undervoltage limit control",
            "  blink        Blink Identify control",
            "",
        ]
    )


def _add_help_option(parser: argparse.ArgumentParser) -> None:
    """Add a custom help option with capitalized help text."""
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
    )


class RootArgumentParser(argparse.ArgumentParser):
    """Root parser with custom help layout for Core and Controls."""

    def format_help(self) -> str:
        return _format_root_help()


class GroupArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with cleaner help for control subcommands."""

    def format_help(self) -> str:
        text = super().format_help()
        text = text.replace("positional arguments:", "Subcommands:")
        text = text.replace("options:", "Option:")
        text = re.sub(
            r"(^Subcommands:\n)\s+SUBCOMMAND\n",
            r"\1",
            text,
            flags=re.MULTILINE,
        )

        subcommands_marker = "\nSubcommands:\n"
        option_marker = "\nOption:\n"

        if subcommands_marker in text and option_marker in text:
            before_option, after_option = text.split(option_marker, 1)
            option_body, subcommands_part = after_option.split(
                subcommands_marker,
                1,
            )

            before_option = before_option.rstrip()
            option_body = option_body.rstrip()
            subcommands_part = subcommands_part.rstrip()

            text = (
                f"{before_option}\n\n"
                f"{option_marker.lstrip()}{option_body}\n\n"
                f"{subcommands_marker.lstrip()}{subcommands_part}\n"
            )

        return text


def build_parser() -> argparse.ArgumentParser:
    """Build the root argparse parser."""
    parser = RootArgumentParser(
        prog="gen",
        description=APP_HELP,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )
    _add_help_option(parser)

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"gen {__version__} ({__release_date__})",
        help="Show the program's version number and exit",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        parser_class=GroupArgumentParser,
    )

    _add_core_commands(subparsers)
    _add_output_group(subparsers)
    _add_blink_group(subparsers)
    _add_foldback_group(subparsers)
    _add_ovp_group(subparsers)
    _add_uvl_group(subparsers)

    return parser


def _configure_group_parser(
    subparsers: AnySubparsers,
    *,
    name: str,
    help_text: str,
    description: str,
    usage: str,
    dest: str,
) -> tuple[GroupArgumentParser, AnySubparsers]:
    """Create a control group parser and its subcommand parser collection."""
    parser = subparsers.add_parser(
        name,
        help=help_text,
        description=description,
        usage=usage,
        formatter_class=argparse.RawTextHelpFormatter,
        add_help=False,
    )
    _add_help_option(parser)

    group_subparsers = parser.add_subparsers(
        dest=dest,
        title="Subcommands",
        metavar="SUBCOMMAND",
        parser_class=GroupArgumentParser,
    )

    parser.set_defaults(func=lambda args, p=parser: p.print_help())
    return parser, group_subparsers


def _add_simple_subcommand(
    subparsers: AnySubparsers,
    name: str,
    help_text: str,
    command: Callable[[], None],
) -> None:
    """Register a leaf subcommand that takes no extra arguments."""
    parser = subparsers.add_parser(
        name,
        help=help_text,
        add_help=False,
    )
    _add_help_option(parser)
    parser.set_defaults(func=lambda args, cmd=command: cmd())


def _add_core_commands(subparsers: AnySubparsers) -> None:
    """Register core top-level commands."""
    from gen.core import (
        connect_command,
        disconnect_command,
        faults_command,
        info_command,
        ping_command,
    )

    parser_connect = subparsers.add_parser(
        "connect",
        help="Select and validate the active target IP",
        add_help=False,
    )
    _add_help_option(parser_connect)
    parser_connect.add_argument("ip", metavar="IP")
    parser_connect.set_defaults(func=lambda args: connect_command(args.ip))

    _add_simple_subcommand(
        subparsers,
        "disconnect",
        "Apply safe shutdown and forget target",
        disconnect_command,
    )
    _add_simple_subcommand(
        subparsers,
        "ping",
        "Check communication with active target",
        ping_command,
    )
    _add_simple_subcommand(
        subparsers,
        "info",
        "Read instrument information",
        info_command,
    )
    _add_simple_subcommand(
        subparsers,
        "faults",
        "Read and decode active faults",
        faults_command,
    )


def _add_output_group(subparsers: AnySubparsers) -> None:
    """Register the output control group."""
    from gen.controls import (
        output_off_command,
        output_on_command,
        output_reset_command,
        output_set_command,
        output_status_command,
    )

    _, output_subparsers = _configure_group_parser(
        subparsers,
        name="output",
        help_text="Output control and setpoints",
        description="Output control and setpoints",
        usage="gen output [-h] SUBCOMMAND [VALUES]",
        dest="output_action",
    )

    _add_simple_subcommand(
        output_subparsers,
        "status",
        "Read current output status",
        output_status_command,
    )

    parser_set = output_subparsers.add_parser(
        "set",
        help="Apply voltage and current setpoints (<voltage> <current>)",
        add_help=False,
    )
    _add_help_option(parser_set)
    parser_set.add_argument("voltage", type=float, metavar="VOLTAGE")
    parser_set.add_argument("current", type=float, metavar="CURRENT")
    parser_set.set_defaults(
        func=lambda args: output_set_command(args.voltage, args.current)
    )

    _add_simple_subcommand(
        output_subparsers,
        "on",
        "Turn output on",
        output_on_command,
    )
    _add_simple_subcommand(
        output_subparsers,
        "off",
        "Turn output off",
        output_off_command,
    )
    _add_simple_subcommand(
        output_subparsers,
        "reset",
        "Apply safe shutdown sequence",
        output_reset_command,
    )


def _add_blink_group(subparsers: AnySubparsers) -> None:
    """Register the blink control group."""
    from gen.controls import blink_off_command, blink_on_command

    _, blink_subparsers = _configure_group_parser(
        subparsers,
        name="blink",
        help_text="Blink Identify control",
        description="Blink Identify control",
        usage="gen blink [-h] SUBCOMMAND",
        dest="blink_action",
    )

    _add_simple_subcommand(
        blink_subparsers,
        "on",
        "Start Blink Identify",
        blink_on_command,
    )
    _add_simple_subcommand(
        blink_subparsers,
        "off",
        "Stop Blink Identify",
        blink_off_command,
    )


def _add_foldback_group(subparsers: AnySubparsers) -> None:
    """Register the foldback control group."""
    from gen.controls import (
        foldback_off_command,
        foldback_on_command,
        foldback_status_command,
    )

    _, foldback_subparsers = _configure_group_parser(
        subparsers,
        name="foldback",
        help_text="Foldback protection control",
        description="Foldback protection control",
        usage="gen foldback [-h] SUBCOMMAND",
        dest="foldback_action",
    )

    _add_simple_subcommand(
        foldback_subparsers,
        "status",
        "Read foldback protection state",
        foldback_status_command,
    )
    _add_simple_subcommand(
        foldback_subparsers,
        "on",
        "Enable foldback protection",
        foldback_on_command,
    )
    _add_simple_subcommand(
        foldback_subparsers,
        "off",
        "Disable foldback protection",
        foldback_off_command,
    )


def _add_ovp_group(subparsers: AnySubparsers) -> None:
    """Register the OVP control group."""
    from gen.controls import ovp_set_command, ovp_status_command

    _, ovp_subparsers = _configure_group_parser(
        subparsers,
        name="ovp",
        help_text="Overvoltage protection control",
        description="Overvoltage protection control",
        usage="gen ovp [-h] SUBCOMMAND [VALUE]",
        dest="ovp_action",
    )

    _add_simple_subcommand(
        ovp_subparsers,
        "status",
        "Read the current OVP setting",
        ovp_status_command,
    )

    parser_set = ovp_subparsers.add_parser(
        "set",
        help="Set the OVP level (<value>)",
        add_help=False,
    )
    _add_help_option(parser_set)
    parser_set.add_argument("value", type=float, metavar="VALUE")
    parser_set.set_defaults(func=lambda args: ovp_set_command(args.value))


def _add_uvl_group(subparsers: AnySubparsers) -> None:
    """Register the UVL control group."""
    from gen.controls import uvl_set_command, uvl_status_command

    _, uvl_subparsers = _configure_group_parser(
        subparsers,
        name="uvl",
        help_text="Undervoltage limit control",
        description="Undervoltage limit control",
        usage="gen uvl [-h] SUBCOMMAND [VALUE]",
        dest="uvl_action",
    )

    _add_simple_subcommand(
        uvl_subparsers,
        "status",
        "Read the current UVL setting",
        uvl_status_command,
    )

    parser_set = uvl_subparsers.add_parser(
        "set",
        help="Set the UVL level (<value>)",
        add_help=False,
    )
    _add_help_option(parser_set)
    parser_set.add_argument("value", type=float, metavar="VALUE")
    parser_set.set_defaults(func=lambda args: uvl_set_command(args.value))


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
Command-line interface handling for scans2any.
"""

import argparse
import platform
import sys
from argparse import OPTIONAL, SUPPRESS, ZERO_OR_MORE, ArgumentDefaultsHelpFormatter
from os import environ

from scans2any.filters import avail_filters
from scans2any.helpers.utils import validate_columns
from scans2any.internal import printer
from scans2any.internal.protocols import HasAddArguments
from scans2any.parsers import (
    avail_parsers,
    parser_custom_columns,
)
from scans2any.writers import avail_writers


class DisplayDefaultsNotNone(ArgumentDefaultsHelpFormatter):
    def _get_help_string(self, action):
        help_string = action.help
        if "%(default)" not in action.help and action.default is not SUPPRESS:
            defaulting_nargs = [OPTIONAL, ZERO_OR_MORE]
            if (
                action.option_strings or action.nargs in defaulting_nargs
            ) and action.default:  # Only add default info if it's not None
                help_string += " (default: %(default)s)"  # NORUFF
        return help_string


def show_info(version):
    """Display logo and application information."""
    import scans2any.parsers as parsers

    # Resolve input formats from parser module (exclude merge_file_parser)
    input_formats = sorted(
        [
            name[:-7]
            for name in dir(parsers)
            if name.endswith("_parser")
            and (name != "merge_file_parser" and name != "auto_parser")
        ]
    )

    # Dynamically resolve output formats from avail_writers
    output_formats = sorted([obj.NAME for obj in avail_writers])

    def format_list(items):
        border = len(items) // 2
        return ", ".join(items[:border]), ", ".join(items[border:])

    input1, input2 = format_list(input_formats)
    output1, output2 = format_list(output_formats)

    gre = "\033[32m"  # green
    yel = "\033[33m"  # yellow
    cya = "\033[36m"  # cyan
    rst = "\033[0m"  # reset
    bold = "\033[1m"  # bold
    nul = ""  # empty, to align string in code

    if environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        cya = "\x1b[38;2;00;153;255m"  # overwrite cyan with softscheck blue

    if platform.system() == "Windows":
        print(f"""\n\
                {bold}scans2any {version}{rst}\n
        {gre} parse and combine scan data to various outputs\n
        {yel} supported input formats:
        {rst}   {input1}
        {nul}   {input2}\n
        {yel} supported output formats:
        {rst}   {output1}
        {rst}   {output2}\n
        {yel} made by:{rst} https://www.soft{bold}{cya}S{rst}check.com\n""")  # noqa: T201
    else:
        print(f"""\n\
        {cya}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ {nul}        {bold}scans2any {version}{rst}
        {cya}⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡿⠋⠀⠀⠀⢀⣴⣿⣿⣿⣿
        {cya}⣿⣿⠈⠻⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠋⠀⠀⠀⢀⣴⣿⣿⠟⠁⣿⣿ {gre} parse and combine scan data to various outputs
        {cya}⣿⣿⠀⠀⠈⠻⣿⣿⣦⡀⢀⣴⠀⠀⠀⠀⢀⣴⣿⣿⠟⠁⠀⠀⣿⣿
        {nul}⣿⣿⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿⠀⠀⢀⣴⣿⣿⠟⠁⠀⠀⠀⣠⣿⣿ {yel} supported input formats:
        {cya}⣿⣿⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⠀⠀⣿⣿⠟⠁⠀⠀⠀⣠⣾⣿⣿⣿ {rst}  {input1}
        {nul}⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀ {nul}  {input2}
        {cya}⣿⣿⣿⡿⠋⠀⠀⠀⢀⣴⣿⣿⠀⠀⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⣿⣿
        {nul}⣿⣿⠋⠀⠀⠀⢀⣴⣿⣿⠟⠁⠀⠀⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⣿⣿ {yel} supported output formats:
        {cya}⣿⣿⠀⠀⢀⣴⣿⣿⠟⠁⠀⠀⠀⠀⠟⠁⠈⠻⣿⣿⣦⡀⠀⠀⣿⣿ {rst}  {output1}
        {cya}⣿⣿⢀⣴⣿⣿⠟⠁⠀⠀⠀⣠⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣦⡀⣿⣿ {rst}  {output2}
        {cya}⣿⣿⣿⣿⠟⠁⠀⠀⠀⣠⣾⣿⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣿⣿⣿⣿
        {nul}⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿ {yel} made by:{rst} https://www.soft{bold}{cya}S{rst}check.com\n""")  # noqa: T201


def print_options(item):
    """Print command-line options for items that have custom arguments."""
    if hasattr(item, "add_arguments"):
        temp_parser = argparse.ArgumentParser(add_help=False)
        item.add_arguments(temp_parser)
        for action in temp_parser._actions:
            opts = ", ".join(action.option_strings)
            print(f"   {opts}:")  # noqa: T201
            if action.default and len(action.default) > 0:
                print(f'     Default: "{action.default}"')  # noqa: T201
            if action.help and action.help != argparse.SUPPRESS:
                print(f"     Help: {action.help}")  # noqa: T201


def list_available_filters():
    """List all available filters with descriptions and options."""
    printer.section("Available filters with custom arguments:")
    for name, obj, _ in avail_filters:
        print(f" * {name}")  # noqa: T201
        print(f"   {obj.apply_filter.__doc__}")  # noqa: T201
        print_options(obj)
        print()  # noqa: T201


def list_available_writers():
    """List all available writers with descriptions and options."""
    printer.section("Available writers with custom arguments:")
    for writer in avail_writers:
        print(f" * {writer.NAME}")  # noqa: T201
        print(f"   {writer.__doc__}")  # noqa: T201
        print_options(writer)
        print()  # noqa: T201


def filter_list(filters):
    """Checks if filters are valid."""
    avail_filter_names = [name for name, _, _ in avail_filters]
    for f in filters:
        if f not in avail_filter_names:
            raise argparse.ArgumentTypeError(
                f"Invalid filter '{f}'. Available filters: {avail_filter_names}"
            )
    return filters[0]


def arg_parser(version):
    """Parse arguments and print usage information if no arguments are given."""

    class LogoArgumentParser(argparse.ArgumentParser):
        def parse_args(self, args=None, namespace=None):
            # If no arguments are provided, show info and usage.
            if len(sys.argv) == 1:
                show_info(version)
                print(self.format_usage())  # noqa: T201
                self.exit(0)
            return super().parse_args(args, namespace)

    parser = LogoArgumentParser(
        prog="scans2any",
        description="Merge infrastructure scans and convert them to various formats.",
        epilog=f"{printer.Colors.HEADER}Examples:{printer.Colors.ENDC}\n"
        + "scans2any --nmap tcp_scan.xml --nmap udp_scan.xml "
        + "--nessus scan.nessus",
        formatter_class=DisplayDefaultsNotNone,
        add_help=False,
    )

    # Add arguments to parser
    _add_basic_arguments(parser)
    _add_scan_arguments(parser)
    _add_writer_arguments(parser)
    _add_verbosity_arguments(parser)
    _add_filter_arguments(parser)

    return parser


def _add_basic_arguments(parser):
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        default=False,
        help="Displays version and exits",
    )
    parser.add_argument(
        "--merge-file",
        metavar="filename",
        help="Use file as merge file to resolve conflicts",
    )
    parser.add_argument(
        "--buffer-file",
        metavar="buffer",
        help="Choose this file to store intermediary results in case the program cannot resolve all conflicts automatically.",
        default="BUFFER_FILE.json",
    )
    parser.add_argument(
        "-o", "--out", metavar="filename", help="output to specified file"
    )
    parser.add_argument(
        "--ignore-conflicts",
        action="store_true",
        default=False,
        help="Do not check for conflicts and do not create a merge file",
    )
    parser.add_argument(
        "--no-auto-merge",
        action="store_true",
        default=False,
        help="Do not apply automatic conflict solving using internal rules",
    )


def _add_scan_arguments(parser):
    scan_group = parser.add_argument_group("input files (at least one required)")

    for name in avail_parsers:
        if hasattr(avail_parsers[name], "add_arguments"):
            avail_parsers[name].add_arguments(scan_group)


def _add_writer_arguments(parser):
    writer_group = parser.add_argument_group("output writer")
    writer_group.add_argument(
        "-w",
        "--writer",
        default="terminal",
        choices=[obj.NAME for obj in avail_writers],
        help="Specify output writer.",
    )
    writer_group.add_argument(
        "--multi-table",
        action="store_true",
        default=False,
        help="Creates one table for each host, if supported by output format",
    )
    default_cols = ("IP-Addresses", "Hostnames", "Ports", "Services", "Banners", "OS")
    writer_group.add_argument(
        "-c",
        "--columns",
        type=lambda s: validate_columns(
            tuple(s.split(",")),
            extra_columns=parser_custom_columns,
            default_columns=default_cols,
        ),
        default=default_cols,
        help="Specify output columns as a comma-separated list. Use + or - to add or remove columns (e.g. +CVE,-OS).",
    )
    writer_group.add_argument(
        "-W",
        "--list-writers",
        action="store_true",
        help="List writers with descriptions and options",
    )


def _add_verbosity_arguments(parser):
    verbosity_group = parser.add_argument_group("verbosity options")
    verbosity_exclusive = verbosity_group.add_mutually_exclusive_group()
    verbosity_exclusive.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity level (use twice for debug mode)",
    )
    verbosity_exclusive.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        default=False,
        help="Suppresses all output except errors",
    )


def _add_filter_arguments(parser):
    filter_group = parser.add_argument_group("filter options")
    filter_group.add_argument(
        "--filters",
        default=[
            "trash_banner",
            "trash_service_name",
            "trash_hostname",
            "combine_banner",
            "nmap_banner",
        ],
        help="Overwrites default filters with specified filters",
        nargs="+",
        type=lambda s: filter_list(s.split(",")),
    )
    filter_group.add_argument(
        "-F",
        "--enable-filters",
        default=[],
        help="Enables additional filters (applied after --filters)",
        nargs="+",
        type=lambda s: filter_list(s.split(",")),
    )
    filter_group.add_argument(
        "--disable-filters",
        default=[],
        help="Disables certain filters (will be applied after --enable-filters)",
        nargs="+",
        type=lambda s: filter_list(s.split(",")),
    )
    filter_group.add_argument(
        "-C",
        "--col",
        nargs="+",
        default=None,
        metavar="col:regex",
        help=(
            "Shorthand for --enable-filters column_filter --column-regex. "
            "Filter hosts/services by column regex. "
            "Syntax: col:regex (match), col:!regex (negate), regex (all columns). "
            "Multiple specs are ANDed. Use (?i) prefix for case-insensitive matching. "
            "Example: -C Services:(?i)http Banners:!N/A"
        ),
    )
    filter_group.add_argument(
        "-Cv",
        "--col-value",
        nargs="*",
        default=None,
        metavar="col:regex",
        help=(
            "Like -C but enables value-level mode: every service must satisfy each "
            "global pattern on its own service-level fields to be kept. "
            "Multi-value fields (Banners, Services, etc.) are trimmed to exact matches. "
            "Specs are optional — '-Cv Services:ssh' is equivalent to "
            "'-C Services:ssh --col-value'."
        ),
    )
    filter_group.add_argument(
        "-Ch",
        "--col-host",
        nargs="*",
        default=None,
        metavar="col:regex",
        help=(
            "Like -C but enables host-level mode: if the host (or any of its services) "
            "satisfies the patterns, the entire host is kept with all its services intact. "
            "Specs are optional."
        ),
    )
    filter_group.add_argument(
        "--hosts-file",
        metavar="filename",
        help="Filter output by a list of IPs or hostnames from a file (one per line)",
        default=None,
    )
    filter_group.add_argument(
        "-L",
        "--list-filters",
        action="store_true",
        help="List filters with descriptions and options",
    )


def parse_args_with_custom_options(
    version: str,
) -> tuple[argparse.ArgumentParser, argparse.Namespace]:
    """Parse args including custom writer and filter options."""
    parser = arg_parser(version)
    known_args, remaining = parser.parse_known_args()

    # Add filter-specific arguments
    filters = list(
        set(known_args.filters + known_args.enable_filters)
        - set(known_args.disable_filters)
    )

    filter_args = parser.add_argument_group("filter arguments")
    for name, obj, _ in avail_filters:
        if hasattr(obj, "add_arguments") and name in filters:
            obj.add_arguments(filter_args)

    # Add writer-specific arguments
    writer_args = parser.add_argument_group("writer arguments")
    for obj in avail_writers:
        if isinstance(obj, HasAddArguments) and known_args.writer == obj.NAME:
            obj.add_arguments(writer_args)

    final_args = parser.parse_args(remaining, namespace=known_args)

    # Handle --col shorthand: enable column_filter and set column_regex
    if final_args.col is not None:
        if "column_filter" not in final_args.enable_filters:
            final_args.enable_filters.append("column_filter")
        # Set column_regex to the provided values
        final_args.column_regex = final_args.col

    # Handle --col-value: accepts optional specs like -C and enables value mode.
    if getattr(final_args, "col_value", None) is not None:
        final_args.col_value_mode = True
        if final_args.col_value:  # non-empty specs given directly to -Cv
            final_args.column_regex = (
                getattr(final_args, "column_regex", []) or []
            ) + final_args.col_value
        if "column_filter" not in final_args.enable_filters:
            final_args.enable_filters.append("column_filter")

    # Handle --col-host: accepts optional specs like -C and enables host mode.
    if getattr(final_args, "col_host", None) is not None:
        final_args.col_host_mode = True
        if final_args.col_host:  # non-empty specs given directly to -Ch
            final_args.column_regex = (
                getattr(final_args, "column_regex", []) or []
            ) + final_args.col_host
        if "column_filter" not in final_args.enable_filters:
            final_args.enable_filters.append("column_filter")

    # Handle --hosts-file shorthand: enable hosts_file_filter
    if (
        final_args.hosts_file is not None
        and "hosts_file_filter" not in final_args.enable_filters
    ):
        final_args.enable_filters.append("hosts_file_filter")

    return parser, final_args

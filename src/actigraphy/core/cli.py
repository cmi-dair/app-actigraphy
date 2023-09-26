"""Command line interface for the actigraphy APP."""
import argparse
import pathlib


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        argparse.Namespace: The parsed command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="""Actigraphy APP to manually correct annotations for the sleep log diary. """,
        epilog="""APP developed by Child Mind Institute.""",
    )
    parser.add_argument("input_folder", help="GGIR output folder", type=pathlib.Path)
    return parser.parse_args()


def get_subject_folders(args: argparse.Namespace) -> list[str]:
    """Returns a list of subject folders sorted by name.

    Args:
        args: The parsed command-line arguments.

    Returns:
        list[str]: A list of subject folders sorted by name.
    """
    input_datapath = args.input_folder
    return [str(x) for x in sorted(input_datapath.glob("output_*"))]

import argparse
import pathlib


def parse_args() -> list[str]:
    """Parse command line arguments.

    Returns:
        A list of strings representing the paths to the subject directories.
    """
    parser = argparse.ArgumentParser(
        description="""Actigraphy APP to manually correct annotations for the sleep log diary. """,
        epilog="""APP developed by Child Mind Institute.""",
    )
    parser.add_argument("input_folder", help="GGIR output folder", type=pathlib.Path)
    args = parser.parse_args()

    input_datapath = args.input_folder
    return [str(x) for x in sorted(input_datapath.glob("output_*"))]

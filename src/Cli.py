import argparse

def build_parser():
    parser = argparse.ArgumentParser(
        prog="unity-safe-analyzer",
        description="Unity Safe Analyzer - Defensive research tool"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to input file"
    )

    parser.add_argument(
        "--output",
        help="Output directory (default: output/reports)"
    )

    parser.add_argument(
        "--scan-strings",
        action="store_true",
        help="Extract readable ASCII strings"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Generate JSON report"
    )

    parser.add_argument(
        "--markdown",
        action="store_true",
        help="Generate Markdown report"
    )

    return parser


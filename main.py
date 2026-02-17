import os
from .cli import build_parser
from .logging_setup import setup_logging
from .config import DEFAULT_OUTPUT_DIR
from .core.utils import calculate_sha256, validate_input
from .core.scanner import scan_strings
from .output.txt_report import generate_txt_report
from .output.json_report import generate_json_report
from .output.markdown_report import generate_markdown_report

def main():
    parser = build_parser()
    args = parser.parse_args()

    setup_logging()

    input_path = args.input
    output_dir = args.output or DEFAULT_OUTPUT_DIR

    validate_input(input_path)

    results = {
        "file": input_path,
        "size_bytes": os.path.getsize(input_path),
        "sha256": calculate_sha256(input_path)
    }

    if args.scan_strings:
        results["strings"] = scan_strings(input_path)

    generate_txt_report(results, output_dir)

    if args.json:
        generate_json_report(results, output_dir)

    if args.markdown:
        generate_markdown_report(results, output_dir)

    print(f"Analysis complete. Reports saved in: {output_dir}")

if __name__ == "__main__":
    main()

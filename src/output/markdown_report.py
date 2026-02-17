import os

def generate_markdown_report(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, "report.md")

    with open(path, "w", encoding="utf-8") as f:
        f.write("# Unity Safe Analyzer Report\n\n")
        for key, value in results.items():
            if key != "strings":
                f.write(f"**{key}**: {value}\n\n")

        if results.get("strings"):
            f.write("## Extracted Strings (Limited)\n\n")
            for s in results["strings"]:
                f.write(f"- {s}\n")

    return path

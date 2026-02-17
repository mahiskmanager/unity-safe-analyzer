import os

def generate_txt_report(results, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "report.txt")

    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=== Unity Safe Analyzer Report ===\n\n")
        for key, value in results.items():
            if key != "strings":
                f.write(f"{key.upper()}: {value}\n")

        if results.get("strings"):
            f.write("\n=== STRINGS (LIMITED) ===\n")
            for s in results["strings"]:
                f.write(s + "\n")

    return report_path

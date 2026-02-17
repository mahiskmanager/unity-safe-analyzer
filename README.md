# Unity Safe Analyzer

Defensive and educational analysis tool for Unity-related files.

## Features

- SHA256 hashing
- File size inspection
- ASCII string extraction (limited)
- TXT / JSON / Markdown reports
- Fully compatible with Termux Android

## Usage (Termux)

chmod +x scripts/*.sh
./scripts/run.sh --input sample.apk --scan-strings --json --markdown

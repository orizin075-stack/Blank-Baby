#!/bin/bash
# Regenerate src/main/resources from the 1.21.1 jar (unzipped at $1) and the Forge templates.
set -e
P=$(cd "$(dirname "$0")" && pwd)
R=$P/src/main/resources
rm -rf "$R"
python3 -I "$P/tools/convert_resources.py" "$1" "$R"
cp -r "$P/templates/." "$R/"

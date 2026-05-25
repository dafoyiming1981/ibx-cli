#!/usr/bin/env python3
"""Regenerate install_ibxcli.sh from current source code."""

import pathlib

ROOT = pathlib.Path(__file__).parent.parent
SRC = ROOT / "src" / "ibxcli"

HEADER = '''#!/usr/bin/env bash
# install_ibxcli.sh — Zero-download installer for ibx-cli
#
# Usage:
#   1. Copy/paste this entire script to the target server
#   2. Run: bash install_ibxcli.sh
#
# Prerequisites:
#   - python3.12 installed
#   - Internal pip source accessible
#
# Installs to: ~/.local/ibxcli/ (no root required)
# Entry point:  ~/.local/bin/ibx (via alias)

set -euo pipefail

INSTALL_DIR="${IBX_INSTALL_DIR:-$HOME/.local/ibxcli}"
SRC_DIR="$INSTALL_DIR/src/ibxcli"
BIN_DIR="$INSTALL_DIR/bin"

echo "=== ibx-cli installer ==="
echo "Install directory: $INSTALL_DIR"
echo ""

# --- Step 1: Install Python dependencies ---
echo "[1/3] Setting up pip for python3.12..."

# System pip may point to python3.6; ensure python3.12 has its own pip
if python3.12 -m pip --version &>/dev/null; then
    echo "  python3.12 -m pip already available."
else
    python3.12 -m ensurepip
fi

python3.12 -m pip install click rich pyyaml infoblox-client --quiet --trusted-host your-internal-pip-mirror

# --- Step 2: Deploy source files ---
echo "[2/3] Deploying source files..."

mkdir -p "$SRC_DIR/cli" "$SRC_DIR/core" "$SRC_DIR/formatters" "$SRC_DIR/objects" "$SRC_DIR/utils"
mkdir -p "$BIN_DIR"

'''

FOOTER = '''
# --- Step 3: Create entry-point script ---
echo "[3/3] Creating entry-point script..."

cat > "$BIN_DIR/ibx" << 'ENTRYEOF'
#!/usr/bin/env python3
import sys
import os

install_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src_dir = os.path.join(install_dir, "src")
sys.path.insert(0, src_dir)

from ibxcli.cli.main import cli

if __name__ == "__main__":
    cli()
ENTRYEOF

chmod +x "$BIN_DIR/ibx"

echo ""
echo "=== Installation complete ==="
echo ""
echo "Add the following alias to your ~/.bashrc:"
echo ""
echo "  alias ibx=\"${BIN_DIR}/ibx\""
echo ""
echo "Or run directly: ${BIN_DIR}/ibx --version"
'''

# Collect all Python source files
py_files = sorted(SRC.rglob("*.py"))

lines = [HEADER]
for f in py_files:
    rel = f.relative_to(SRC)
    comment = f"# ===== ibxcli/{rel} ====="
    target = f'cat > "$SRC_DIR/{rel}" << \'PYEOF\''
    content = f.read_text()
    lines.append(comment)
    lines.append(target)
    lines.append(content)
    lines.append("PYEOF")
    lines.append("")

lines.append(FOOTER)

output = ROOT / "dist" / "install_ibxcli.sh"
output.write_text("\n".join(lines))
print(f"Wrote {output} ({len(lines)} lines)")

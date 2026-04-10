#!/usr/bin/env bash
# Agent-8 CLI workflow — uses conda env human_traffic.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v conda &>/dev/null; then
  echo "conda not found. Install Miniconda/Anaconda or add conda to PATH."
  exit 1
fi

# shellcheck source=/dev/null
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate human_traffic

exec python main.py "$@"

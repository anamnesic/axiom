#!/usr/bin/env bash
# Chronokairo AXIOM — Quick Bash Setup Launcher
# Usage:
#   ./setup.sh --min
#   ./setup.sh --full
#   ./setup.sh --custom
#   ./setup.sh --select cas,docs,lean
#   ./setup.sh --check

set -e

python3 setup_env.py "$@"

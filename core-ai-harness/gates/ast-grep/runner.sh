#!/usr/bin/env bash
# ast-grep runner - simple wrapper for ast-grep scan
# Output: raw JSON from ast-grep (parsed by gate_runner.py)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SGCONFIG="$SCRIPT_DIR/sgconfig.yml"

# Check if ast-grep is available
if command -v ast-grep &> /dev/null; then
    AST_GREP_CMD="ast-grep"
elif command -v sg &> /dev/null; then
    AST_GREP_CMD="sg"
else
    echo "Error: ast-grep not found. Install with: brew install ast-grep" >&2
    exit 1
fi

# If no args, show usage
if [ $# -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] [...]" >&2
    echo "       $0 --config <config.yaml> <file1> [file2] [...]" >&2
    exit 1
fi

# Parse args
CONFIG_FILE="$SGCONFIG"
FILES=()

while [ $# -gt 0 ]; do
    case "$1" in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        *)
            FILES+=("$1")
            shift
            ;;
    esac
done

if [ ${#FILES[@]} -eq 0 ]; then
    echo "Error: No files specified" >&2
    exit 1
fi

# Run ast-grep with JSON output
# Exit code: 0 = no issues, 1 = issues found (not an error)
"$AST_GREP_CMD" scan \
    --config "$CONFIG_FILE" \
    --json \
    "${FILES[@]}" 2>/dev/null || true

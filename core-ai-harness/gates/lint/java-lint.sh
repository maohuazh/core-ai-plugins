#!/usr/bin/env bash
# Java lint gate (FBR profile, optional).
#
# Runs the FBR JavaLint tool against the given Java files.
# Requires the prebuilt JAR deployed to gates/lint/.dist/java-lint.jar
# by the gate-install command (the JAR is NOT shipped in the repo:
# it is ~25MB and FBR-specific).
#
# Exit codes:
#   0 - clean
#   1 - findings
#   2 - JAR missing (gate not installed)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR="$SCRIPT_DIR/.dist/java-lint.jar"

if [ ! -f "$JAR" ]; then
  echo "java-lint gate: java-lint.jar not found in gates/lint/.dist/." >&2
  echo "Deploy it with: /gate-install --kit /path/to/fbr-agent-gates" >&2
  exit 2
fi

exec java -jar "$JAR" "$@"

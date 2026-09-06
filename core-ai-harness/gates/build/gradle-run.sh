#!/usr/bin/env bash
# Gradle build gate (FBR profile, optional).
#
# Runs a Gradle build via gradle-runner.py which projects a compact,
# high-signal diagnostic summary. Logs are retained in /tmp/fbr-gradle.
#
# Exit codes:
#   0 - build succeeded / no issues
#   1 - build issues found
#   2 - prerequisites missing (no gradlew wrapper)
#
# Must be run from a Gradle project root that provides ./gradlew.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f ./gradlew ]; then
  echo "build gate: ./gradlew not found in current directory." >&2
  echo "Run this gate from the Gradle project root." >&2
  exit 2
fi

exec python3 "${SCRIPT_DIR}/gradle-runner.py" "$@"

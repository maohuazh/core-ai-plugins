#!/usr/bin/env bash
# Local Error Prone gate (FBR profile, optional).
#
# Runs the FBR Error Prone scanner against the given Java files.
# Requires the prebuilt JAR deployed to gates/error-prone/.dist/error-prone.jar
# by the gate-install command (the JAR is NOT shipped in the repo:
# it is ~24MB and FBR-specific).
#
# The --add-exports flags are required because Error Prone drives
# jdk.compiler in-process.
#
# Exit codes:
#   0 - clean
#   1 - findings
#   2 - JAR missing (gate not installed)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JAR="$SCRIPT_DIR/.dist/error-prone.jar"

if [ ! -f "$JAR" ]; then
  echo "error-prone gate: error-prone.jar not found in gates/error-prone/.dist/." >&2
  echo "Deploy it with: /gate-install --kit /path/to/fbr-agent-gates" >&2
  exit 2
fi

exec java \
  --add-exports=jdk.compiler/com.sun.tools.javac.api=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.file=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.main=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.model=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.processing=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.parser=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.tree=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.util=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.code=ALL-UNNAMED \
  --add-exports=jdk.compiler/com.sun.tools.javac.comp=ALL-UNNAMED \
  --sun-misc-unsafe-memory-access=allow \
  -jar "$JAR" "$@"

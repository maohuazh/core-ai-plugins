#!/usr/bin/env python3
"""
Stop hook - lightweight session-end reminder (DEFAULT OFF).

IMPORTANT: Stop fires at the END OF EVERY TURN, not at session end.
This hook is intentionally disabled by default in hooks.json.

If enabled, it performs a LIGHTWEIGHT check only:
- Checks whether this session has unresolved gate ERROR findings
- Returns a decision:block with a short reason to remind Claude
- MUST check `stop_hook_active` input to avoid infinite loops
  (system blocks after 8 consecutive Stop blocks per turn)

For full session reports, use SessionEnd instead.
"""

import json
import sys
from pathlib import Path

# Add parent directory to Python path so we can import _lib
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Entry point for Stop hook (lightweight version)."""
    # Read hook input
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # CRITICAL: check stop_hook_active to prevent infinite loops
    if not hook_input.get("stop_hook_active", False):
        # Claude Code is in a stop-hook loop guard; do nothing
        sys.exit(0)

    # Lightweight check: look for the session gate state marker
    # (created by post_edit_gate.py when it blocks an edit)
    session_state = Path(f"/tmp/core-ai-harness-{hook_input.get('session_id', 'unknown')}.json")

    if session_state.exists():
        try:
            state = json.loads(session_state.read_text(encoding="utf-8"))
            pending_errors = state.get("pending_errors", 0)
            if pending_errors > 0:
                output = {
                    "decision": "block",
                    "reason": (
                        f"⚠️ {pending_errors} gate violation(s) from this session "
                        "are still unresolved. Run /gates or /gate-fixer to check."
                    ),
                }
                print(json.dumps(output))
                sys.exit(0)
        except Exception:
            pass

    # No pending issues, allow stop
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Never let the hook fail
        sys.exit(0)

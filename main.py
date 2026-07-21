"""
main.py
-------
Entry point for AIDA – AI Desktop Assistant.

Usage:
    python main.py          # Launch with GUI dashboard
    python main.py --cli    # Launch in CLI/voice-only mode

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import argparse
import sys


def main() -> None:
    """Launch AIDA in GUI or CLI mode."""

    parser = argparse.ArgumentParser(
        description="AIDA – AI Desktop Assistant",
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in CLI mode (voice-only, no GUI)",
    )
    args = parser.parse_args()

    if args.cli:
        # ── CLI Mode ─────────────────────────────────────────
        print("\n🤖 AIDA – AI Desktop Assistant (CLI Mode)\n")
        print("Initializing... this may take a moment.\n")

        from app.assistant.assistant import Assistant

        assistant = Assistant()

        try:
            assistant.run()
        except KeyboardInterrupt:
            print("\nGoodbye!")
            sys.exit(0)

    else:
        # ── GUI Mode ─────────────────────────────────────────
        from app.gui.app import AidaApp

        app = AidaApp()
        app.mainloop()


if __name__ == "__main__":
    main()
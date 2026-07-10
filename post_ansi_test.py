"""
post_ansi_test.py — MANUAL test harness for Discord ANSI code blocks.

Why this exists
---------------
ANSI colored text in Discord can ONLY be confirmed by looking at a rendered
message in a real client, so this script posts a labeled set of swatches to the
`testpoint` webhook(s) from .env and then hands off to you for eyeballing.

What the earlier attempts almost certainly got wrong
----------------------------------------------------
1. The real ESC byte was never emitted. Discord needs the raw control
   character U+001B (ESC). You cannot type it, and writing the literal text
   "\\033[" or "[0;31m" into the string just shows those characters. In Python
   you must produce the actual byte via "\\u001b" / "\\033" / "\\x1b".
   (When `requests` serializes the payload, json.dumps encodes that byte as the
   JSON escape "\\u001b" in the wire body, and Discord decodes it back to ESC —
   that round-trip is fine.)
2. The block used plain ``` instead of ```ansi. Without the `ansi` language
   tag Discord treats the escape codes as literal text.
3. It was viewed on an older mobile client. ANSI renders on desktop, web, and
   modern mobile apps; very old mobile shows plain monospace (still readable,
   just no color) — never a hard failure.

Supported palette (this is the WHOLE set — no 256-color, no truecolor):
    styles: 0 reset · 1 bold · 4 underline
    fg:     30 gray 31 red 32 green 33 yellow 34 blue 35 pink 36 cyan 37 white
    bg:     40 dark 41 orange 42 marble 43 gray 44 gray 45 indigo 46 gray 47 white

Run: python post_ansi_test.py            # posts to testpoint
     python post_ansi_test.py --dry      # print payload only, no post
"""

import os
import sys
import json
from dotenv import load_dotenv

from sumo_hooks import post_webhook

# ── ANSI helper (reusable — promote into sumo_data.py if the experiment sticks) ──

ESC = ""          # the real ESC byte — the whole trick lives here
RESET = f"{ESC}[0m"

STYLE = {"normal": 0, "bold": 1, "underline": 4}
FG = {"gray": 30, "red": 31, "green": 32, "yellow": 33,
      "blue": 34, "pink": 35, "cyan": 36, "white": 37}
BG = {"dark": 40, "orange": 41, "marble": 42, "gray": 43,
      "blue_gray": 44, "indigo": 45, "silver": 46, "white": 47}


def ansi(text, fg=None, bg=None, style=None):
    """Wrap text in a Discord-supported ANSI sequence. Params combine as style;fg;bg."""
    codes = []
    if style is not None:
        codes.append(str(STYLE[style]))
    if fg is not None:
        codes.append(str(FG[fg]))
    if bg is not None:
        codes.append(str(BG[bg]))
    if not codes:
        return text
    return f"{ESC}[{';'.join(codes)}m{text}{RESET}"


def block(body: str) -> str:
    """Wrap body in an ```ansi code block."""
    return f"```ansi\n{body}\n```"


# ── Demo content ─────────────────────────────────────────────────

def swatches_block() -> str:
    lines = ["Foreground colors:"]
    for name in FG:
        lines.append(ansi(f"  {name:<8} the quick brown fox", fg=name))
    lines.append("")
    lines.append("Styles:")
    lines.append(ansi("  bold yellow", fg="yellow", style="bold"))
    lines.append(ansi("  underline cyan", fg="cyan", style="underline"))
    lines.append("")
    lines.append("Background + foreground combos:")
    lines.append(ansi("  gold on dark ", fg="yellow", bg="dark", style="bold"))
    lines.append(ansi("  white on red ", fg="white", bg="orange", style="bold"))
    lines.append(ansi("  green on gray ", fg="green", bg="gray"))
    return block("\n".join(lines))


def sumo_demo_block() -> str:
    """A realistic slice of a match card, colored the way we'd actually ship it."""
    title = ansi("N DAY 8 CARD", fg="yellow", style="bold")
    header = ansi("RANK  NAME            W-L  FORM", fg="gray")
    yokozuna = ansi("Y1e   Onosato        7-0  ○○○○○", fg="yellow", style="bold")
    kadoban = ansi("O1w   Kotozakura     3-4  ●○●●○", fg="red")
    normal = "M4e   Atamifuji      5-2  ○○●○○"
    streak = ansi("M9w   Kusano         7-0  ○○○○○", fg="green", style="bold")
    return block("\n".join([title, "", header, yokozuna, kadoban, normal, streak]))


def control_block() -> str:
    """Same escape codes but in a PLAIN block — proves the codes are invisible/handled,
    and gives a side-by-side for 'is my client rendering ansi at all?'."""
    body = ansi("If you can read the escape codes as text here, your client "
                "is NOT rendering ansi.", fg="red")
    return f"```\n{body}\n```"


def build_payload() -> dict:
    description = "\n".join([
        "**1 — Color swatches** (every supported color)",
        swatches_block(),
        "**2 — Sumo card, colored for real**",
        sumo_demo_block(),
        "**3 — Control: same codes in a plain block**",
        control_block(),
    ])
    return {
        "username": "Sumo-hooks (ANSI test)",
        "content": "ANSI render test — check on **desktop/web** and **mobile**.",
        "embeds": [
            {
                "title": "Discord ANSI code block test",
                "description": description,
                "color": 0xE8B923,
            }
        ],
    }


if __name__ == "__main__":
    load_dotenv()
    payload = build_payload()

    # Show the raw ESC byte is present (repr makes \x1b visible).
    print("Sanity check — first swatch line repr (look for \\x1b):")
    print(repr(ansi("  red the quick brown fox", fg="red")))
    print()

    if "--dry" in sys.argv:
        print(json.dumps(payload, indent=2))
        print("\n[dry run] not posted.")
        sys.exit(0)

    testpoint = os.getenv("testpoint", "").split(",")
    if not any(t.strip() for t in testpoint):
        print("No `testpoint` webhook configured in .env — aborting.")
        sys.exit(1)

    post_webhook(payload, testpoint)
    print("Posted to testpoint. Now eyeball it:")
    print("  • Desktop/web: swatches + sumo card should be COLORED.")
    print("  • Mobile: colored on modern apps; plain monospace (still readable) on old ones.")
    print("  • Block 3 (control) should show NO visible escape codes and NO color.")

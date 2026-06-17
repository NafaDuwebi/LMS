#!/usr/bin/env python3
"""
PL Projects LMS – Brand Alignment Script
=========================================
Aligns the LMS colour scheme and logo with the official PL Projects website
(https://plprojects.co.uk).

HOW TO RUN
----------
  1. Open a terminal in the plp_lms/ directory (same folder as main.py).
  2. Run:  python rebrand_plp.py
  3. Restart the FastAPI server:  uvicorn main:app --reload

WHAT THIS SCRIPT DOES
---------------------
  Step 1  Downloads the official PL Projects white-text logo and saves it to
          static/img/plp_logo.svg  (used in the dark navbar).

  Step 2  Replaces brand colours across every HTML template:
            #1A2B4A  →  #540032   (dark navy  → PLP deep burgundy)
            #C9912B  →  #FFC000   (amber      → PLP gold)
            #2A3F6A  →  #6B0040   (navy-light → burgundy-light)
            #b47d24  →  #D4A000   (amber hover → gold hover)

  Step 3  Patches base.html:
            • Replaces the graduation-cap icon + "PLP LMS" text in the navbar
              with the actual PL Projects logo image.
            • Adds a website link to the footer.

  Step 4  Injects a tiny CSS rule into base.html so that gold (#FFC000)
          buttons automatically use dark text (required for WCAG AA contrast —
          bright gold with white text is unreadable).

SAFETY
------
  • Only .html template files are touched — no Python, SQL or config files.
  • The script is idempotent: safe to run more than once.
  • Every changed file is listed in the output.
  • If the logo download fails the script continues; replace
    static/img/plp_logo.svg manually with the PL Projects white-text logo.

BRAND COLOURS (extracted from plprojects.co.uk, June 2026)
-----------------------------------------------------------
  Primary  #540032   rgb(84, 0, 50)     Deep burgundy
  Accent   #FFC000   rgb(255, 192, 0)   PL Projects gold
  P-Light  #6B0040   (burgundy lighter) Used for mobile menu background
  Hover    #D4A000   Darker gold for button hover states
  Body     #403C47   Dark charcoal body text
  BtnText  #35313B   Dark text on gold buttons
"""

import re
import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────

# When run as  python rebrand_plp.py  from inside plp_lms/, __file__ gives us
# the plp_lms/ directory automatically.
BASE_DIR   = Path(__file__).resolve().parent   # …/plp_lms/
TMPL_DIR   = BASE_DIR / "templates"
STATIC_IMG = BASE_DIR / "static" / "img"
BASE_HTML  = TMPL_DIR / "base.html"
LOGO_PATH  = STATIC_IMG / "plp_logo.svg"

# ── Brand colour replacement map ──────────────────────────────────────────────
# Ordered most-specific first to avoid double-replacement.

COLOUR_MAP = [
    # Hover / pressed button tones  (must come before the base hex)
    ("#b47d24",                 "#D4A000"),
    ("#B47D24",                 "#D4A000"),

    # rgba() occurrences — swap the RGB part only, preserve alpha
    ("rgba(201, 145, 43",       "rgba(255, 192, 0"),

    # Tailwind arbitrary-value classes  e.g. bg-[#C9912B] text-[#1A2B4A]
    ("[#C9912B]",               "[#FFC000]"),
    ("[#1A2B4A]",               "[#540032]"),
    ("[#2A3F6A]",               "[#6B0040]"),

    # Inline style / plain hex occurrences
    ("#C9912B",                 "#FFC000"),
    ("#1A2B4A",                 "#540032"),
    ("#2A3F6A",                 "#6B0040"),
]

# ── Logo ───────────────────────────────────────────────────────────────────────
# The SVG logo (three gold chevrons + "PL Projects" white text) is already saved
# at static/img/plp_logo.svg — no download needed.
LOGO_URL = None   # kept for reference; SVG is embedded directly


# ═════════════════════════════════════════════════════════════════════════════
# Step 1 – Logo download
# ═════════════════════════════════════════════════════════════════════════════

def download_logo() -> bool:
    """Check the SVG logo is present in static/img/."""
    STATIC_IMG.mkdir(parents=True, exist_ok=True)

    if LOGO_PATH.exists() and LOGO_PATH.stat().st_size > 100:
        print(f"  ✓ Logo found at {LOGO_PATH}  ({LOGO_PATH.stat().st_size} bytes)")
        return True

    print(f"  ✗ Logo file not found at: {LOGO_PATH}")
    print("    The file plp_logo.svg should have been created alongside this script.")
    print("    Check the static/img/ directory and re-run if needed.")
    return False


# ═════════════════════════════════════════════════════════════════════════════
# Step 2 – Recolour all HTML templates
# ═════════════════════════════════════════════════════════════════════════════

def recolour_file(path: Path) -> int:
    """
    Apply all colour substitutions to a single file.
    Returns the number of replacements made (0 = file unchanged).
    """
    original = path.read_text(encoding="utf-8", errors="replace")
    updated  = original
    for old, new in COLOUR_MAP:
        updated = updated.replace(old, new)
    if updated == original:
        return 0
    path.write_text(updated, encoding="utf-8")
    return sum(original.count(old) for old, _ in COLOUR_MAP)


def recolour_templates() -> dict:
    """
    Walk every .html file under templates/ and apply colour replacements.
    Returns {relative_path: replacement_count} for changed files.
    """
    changed = {}
    for html_file in sorted(TMPL_DIR.rglob("*.html")):
        n = recolour_file(html_file)
        if n:
            changed[html_file.relative_to(BASE_DIR)] = n
    return changed


# ═════════════════════════════════════════════════════════════════════════════
# Step 3 – Patch base.html (logo + footer link)
# ═════════════════════════════════════════════════════════════════════════════

def patch_base_html_logo():
    """
    Replace the graduation-cap icon + 'PLP LMS' text in the navbar with the
    real PL Projects logo image.  Falls back gracefully if the image is absent.
    """
    text = BASE_HTML.read_text(encoding="utf-8")

    # Guard — only patch once
    if "plp_logo.svg" in text:
        print("  ✓ Navbar logo already patched — skipping.")
        return

    # The exact navbar logo block in base.html (whitespace-sensitive match)
    old_block = (
        '<a href="/dashboard" class="flex items-center space-x-2 shrink-0 mr-6">\n'
        '                    <i class="fas fa-graduation-cap text-accent text-lg"></i>\n'
        '                    <span class="text-lg font-bold tracking-tight whitespace-nowrap">PLP LMS</span>\n'
        '                </a>'
    )

    new_block = (
        '<a href="/dashboard" class="flex items-center shrink-0 mr-6">\n'
        '                    <img src="/static/img/plp_logo.svg"\n'
        '                         alt="PL Projects"\n'
        '                         class="h-10 w-auto object-contain"\n'
        '                         title="PL Projects Learning Management System">\n'
        '                </a>'
    )

    if old_block in text:
        text = text.replace(old_block, new_block)
        print("  ✓ Navbar logo replaced with PL Projects image.")
    else:
        # Flexible fallback: try a loose regex in case indentation differs
        pattern = (
            r'<a href="/dashboard"[^>]*class="flex items-center[^"]*shrink-0[^>]*>\s*'
            r'<i class="fas fa-graduation-cap[^"]*"></i>\s*'
            r'<span[^>]*>PLP LMS</span>\s*</a>'
        )
        replacement = (
            '<a href="/dashboard" class="flex items-center shrink-0 mr-6">\n'
            '                    <img src="/static/img/plp_logo.svg" '
            'alt="PL Projects" class="h-10 w-auto object-contain" '
            'title="PL Projects Learning Management System">\n'
            '                </a>'
        )
        new_text, n = re.subn(pattern, replacement, text, flags=re.DOTALL)
        if n:
            text = new_text
            print("  ✓ Navbar logo replaced (via regex fallback).")
        else:
            print("  ⚠  Could not locate navbar logo block — patch skipped.")
            print("    Manually replace the graduation-cap <a> block in base.html.")

    BASE_HTML.write_text(text, encoding="utf-8")


def patch_base_html_footer():
    """Add plprojects.co.uk link to the LMS footer."""
    text = BASE_HTML.read_text(encoding="utf-8")

    old_footer = (
        '<p class="text-sm text-gray-300">&copy; 2026 PL Projects Ltd. All rights reserved.</p>'
    )
    new_footer = (
        '<p class="text-sm text-gray-300">'
        '&copy; 2026 PL Projects Ltd. All rights reserved. '
        '&nbsp;|&nbsp; '
        '<a href="https://plprojects.co.uk" target="_blank" rel="noopener noreferrer" '
        'class="underline hover:text-white transition">'
        'plprojects.co.uk</a></p>'
    )

    if old_footer in text:
        text = text.replace(old_footer, new_footer)
        BASE_HTML.write_text(text, encoding="utf-8")
        print("  ✓ Footer link to plprojects.co.uk added.")
    else:
        print("  ✓ Footer already updated (or text differs) — skipping.")


# ═════════════════════════════════════════════════════════════════════════════
# Step 4 – Button contrast CSS
# ═════════════════════════════════════════════════════════════════════════════

def add_button_contrast_css():
    """
    Inject a CSS rule so all #FFC000 (gold) background elements automatically
    use dark text (#35313B).  Bright gold with white text fails WCAG AA.
    Also ensures gold buttons get the correct darker hover colour.
    Only inserted once (idempotent).
    """
    text = BASE_HTML.read_text(encoding="utf-8")

    MARKER = "/* PLP brand: gold-button contrast */"
    if MARKER in text:
        print("  ✓ Button contrast CSS already present — skipping.")
        return

    css_injection = (
        f"        {MARKER}\n"
        "        /* Gold (#FFC000) needs dark text for WCAG AA contrast */\n"
        "        [style*='background-color: #FFC000'],\n"
        "        [style*='background-color:#FFC000'] {\n"
        "            color: #35313B !important;\n"
        "        }\n"
        "        /* Hover: slightly darker gold */\n"
        "        [style*='background-color: #FFC000']:hover,\n"
        "        [style*='background-color:#FFC000']:hover {\n"
        "            background-color: #D4A000 !important;\n"
        "            color: #35313B !important;\n"
        "        }\n"
    )

    # Insert immediately before the closing </style> tag
    if "    </style>" in text:
        text = text.replace("    </style>", css_injection + "    </style>", 1)
        BASE_HTML.write_text(text, encoding="utf-8")
        print("  ✓ Gold-button dark-text contrast CSS injected into base.html.")
    else:
        print("  ⚠  Could not locate </style> in base.html — CSS not injected.")
        print("    Add the following manually inside the <style> block:")
        print(css_injection)


# ═════════════════════════════════════════════════════════════════════════════
# Entry point
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     PL Projects LMS – Brand Alignment Script  v1.0      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()

    # Sanity check — must find templates/base.html
    if not BASE_HTML.exists():
        print(f"ERROR: base.html not found at:\n  {BASE_HTML}")
        print()
        print("Make sure you run this script from inside the plp_lms/ directory:")
        print("  cd path/to/plp_lms")
        print("  python rebrand_plp.py")
        sys.exit(1)

    # ── Step 1 ─────────────────────────────────────────────────────────────
    print("Step 1/4  Downloading PL Projects logo")
    print("─" * 60)
    logo_ok = download_logo()

    # ── Step 2 ─────────────────────────────────────────────────────────────
    print()
    print("Step 2/4  Replacing brand colours in HTML templates")
    print("─" * 60)
    changed = recolour_templates()
    if changed:
        for path, count in changed.items():
            print(f"  ✓ {path}  ({count} replacement{'s' if count != 1 else ''})")
        print(f"\n  {len(changed)} template file(s) updated.")
    else:
        print("  No colour changes were needed (already up to date).")

    # ── Step 3 ─────────────────────────────────────────────────────────────
    print()
    print("Step 3/4  Patching base.html (navbar logo + footer)")
    print("─" * 60)
    patch_base_html_logo()
    patch_base_html_footer()

    # ── Step 4 ─────────────────────────────────────────────────────────────
    print()
    print("Step 4/4  Injecting button contrast CSS")
    print("─" * 60)
    add_button_contrast_css()

    # ── Summary ────────────────────────────────────────────────────────────
    print()
    print("═" * 60)
    print("  COMPLETE")
    print("═" * 60)
    print()
    print("  Colour changes applied:")
    print("    #1A2B4A (navy)       →  #540032 (PLP burgundy)")
    print("    #C9912B (amber)      →  #FFC000 (PLP gold)")
    print("    #2A3F6A (navy-light) →  #6B0040 (burgundy-light)")
    print("    #b47d24 (hover)      →  #D4A000 (gold-hover)")
    print()
    if logo_ok:
        print(f"  Logo: ✓ {LOGO_PATH}")
    else:
        print(f"  Logo: ✗ Not found — check static/img/plp_logo.svg")
    print()
    print("  ➜  Restart FastAPI to see all changes:")
    print("       uvicorn main:app --reload")
    print()


if __name__ == "__main__":
    main()

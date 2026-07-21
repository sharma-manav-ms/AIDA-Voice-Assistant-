"""
themes.py
---------
Color schemes and typography for the AIDA GUI.
Implements Stitch's 'Aura Kinetic' Cognitive Luminance design system.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """A complete color theme definition based on Stitch Aura Kinetic design system."""

    name: str

    # ── Window & Surfaces ─────────────────────────────────────
    bg_primary: str          # Abyssal Navy canvas (#0A0E27)
    bg_secondary: str        # Surface Container Low (#161A33)
    bg_tertiary: str         # Surface Container (#1A1E37)
    bg_card: str             # Surface Container High (#242842)
    bg_hover: str            # Surface Container Highest (#2F334E)

    # ── Text & Typography ────────────────────────────────────
    text_primary: str        # High contrast headline/body (#DEE0FF)
    text_secondary: str      # Subtitles / secondary metadata (#C7C4D8)
    text_muted: str          # Muted labels (#918FA1)
    text_placeholder: str    # Input placeholder (#464555)

    # ── Brand Accents & Luminance ─────────────────────────────
    accent: str              # Electric Indigo (#4F46E5)
    accent_hover: str        # Indigo Light (#6366F1)
    accent_glow: str         # Indigo Glow rgba
    secondary_accent: str    # Neon Cyan (#06B6D4)
    secondary_glow: str      # Cyan Light (#4CD7F6)

    # ── Semantic Status Colors ────────────────────────────────
    success: str             # #10B981
    warning: str             # #F59E0B
    error: str               # #EF4444
    info: str                # #06B6D4

    # ── Borders & Outlines ────────────────────────────────────
    border: str              # Stroke (#2F334E)
    border_active: str       # Active Glow Stroke (#4F46E5)

    # ── Message Bubbles ──────────────────────────────────────
    user_bubble: str         # Electric Indigo container (#4F46E5)
    user_text: str           # White (#FFFFFF)
    assistant_bubble: str     # Glassmorphic surface container (#1A1E37)
    assistant_text: str      # Ice white (#DEE0FF)

    # ── Status Colors ────────────────────────────────────────
    status_idle: str         # #918FA1
    status_listening: str    # Neon Cyan (#4CD7F6)
    status_thinking: str     # Indigo Light (#6366F1)
    status_speaking: str     # Cyan (#06B6D4)
    status_error: str        # Coral Red (#EF4444)


# ── Aura Kinetic Dark Theme (Primary Stitch Design) ─────────────────────

DARK = Theme(
    name="dark",

    bg_primary="#0A0E27",
    bg_secondary="#161A33",
    bg_tertiary="#1A1E37",
    bg_card="#242842",
    bg_hover="#2F334E",

    text_primary="#DEE0FF",
    text_secondary="#C7C4D8",
    text_muted="#918FA1",
    text_placeholder="#464555",

    accent="#4F46E5",
    accent_hover="#6366F1",
    accent_glow="#3323CC",
    secondary_accent="#06B6D4",
    secondary_glow="#4CD7F6",

    success="#10B981",
    warning="#F59E0B",
    error="#EF4444",
    info="#06B6D4",

    border="#2F334E",
    border_active="#4F46E5",

    user_bubble="#4F46E5",
    user_text="#FFFFFF",
    assistant_bubble="#1A1E37",
    assistant_text="#DEE0FF",

    status_idle="#918FA1",
    status_listening="#4CD7F6",
    status_thinking="#6366F1",
    status_speaking="#06B6D4",
    status_error="#EF4444",
)


# ── Aura Kinetic Light Theme ────────────────────────────────────────────

LIGHT = Theme(
    name="light",

    bg_primary="#F8FAFC",
    bg_secondary="#FFFFFF",
    bg_tertiary="#F1F5F9",
    bg_card="#E2E8F0",
    bg_hover="#CBD5E1",

    text_primary="#0F172A",
    text_secondary="#475569",
    text_muted="#64748B",
    text_placeholder="#94A3B8",

    accent="#4F46E5",
    accent_hover="#4338CA",
    accent_glow="#EEF2FF",
    secondary_accent="#0891B2",
    secondary_glow="#06B6D4",

    success="#059669",
    warning="#D97706",
    error="#DC2626",
    info="#0891B2",

    border="#E2E8F0",
    border_active="#4F46E5",

    user_bubble="#4F46E5",
    user_text="#FFFFFF",
    assistant_bubble="#F1F5F9",
    assistant_text="#0F172A",

    status_idle="#94A3B8",
    status_listening="#059669",
    status_thinking="#D97706",
    status_speaking="#0891B2",
    status_error="#DC2626",
)


# ── Theme Map ────────────────────────────────────────────────────

THEMES: dict[str, Theme] = {
    "dark": DARK,
    "light": LIGHT,
}


def get_theme(name: str = "dark") -> Theme:
    """Return a theme by name. Defaults to dark Aura Kinetic."""
    return THEMES.get(name, DARK)


# ── Font Config ──────────────────────────────────────────────────

FONT_FAMILY_HEADLINE = "Sora"
FONT_FAMILY_BODY = "Inter"
FONT_FAMILY_LABEL = "Segoe UI"
FONT_FAMILY_MONO = "Cascadia Code"

# Backward compatibility alias
FONT_FAMILY = "Segoe UI"

FONT_SIZE_SMALL = 11
FONT_SIZE_NORMAL = 13
FONT_SIZE_LARGE = 16
FONT_SIZE_TITLE = 22
FONT_SIZE_HEADER = 28

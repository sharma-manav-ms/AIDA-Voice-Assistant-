"""
router.py
---------
Command dispatch engine.

Maps spoken text to handler functions using keyword matching,
fuzzy matching (RapidFuzz), and LLM-based intent classification
as a final fallback.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.utils.constants import CommandCategory
from app.utils.helpers import extract_keywords, fuzzy_match, extract_target
from app.utils.logger import get_logger

logger = get_logger(__name__)


# ── Data structures ──────────────────────────────────────────────

@dataclass
class CommandResult:
    """Value object returned by the router."""

    category: CommandCategory
    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    response: str = ""
    success: bool = True


@dataclass
class RegisteredCommand:
    """A single command entry in the registry."""

    category: CommandCategory
    name: str
    keywords: list[str]
    handler: Callable[..., str]
    extract_args: bool = True  # whether to pass remaining text as arg


# ── Router ───────────────────────────────────────────────────────

class CommandRouter:
    """
    Central command dispatch.

    Resolution order:
        1. Exact keyword prefix match
        2. Fuzzy match (RapidFuzz, threshold 65)
        3. LLM intent fallback (if configured)
    """

    def __init__(self) -> None:
        self._commands: list[RegisteredCommand] = []
        self._keyword_map: dict[str, RegisteredCommand] = {}
        self._llm_fallback: Optional[Callable] = None

    # ── Registration ─────────────────────────────────────────

    def register(
        self,
        category: CommandCategory,
        name: str,
        keywords: list[str],
        handler: Callable[..., str],
        extract_args: bool = True,
    ) -> None:
        """
        Register a command handler.

        Parameters
        ----------
        category : CommandCategory
            Which module owns this command.
        name : str
            Human-readable command name (for logging).
        keywords : list[str]
            Trigger phrases. The first matching keyword wins.
        handler : callable
            Function to execute. Receives extracted text as first arg
            if *extract_args* is True.
        extract_args : bool
            If True, the text remaining after the keyword is passed
            to the handler as a positional argument.
        """

        cmd = RegisteredCommand(
            category=category,
            name=name,
            keywords=[kw.lower() for kw in keywords],
            handler=handler,
            extract_args=extract_args,
        )

        self._commands.append(cmd)

        for kw in cmd.keywords:
            self._keyword_map[kw] = cmd

        logger.debug("Registered command: %s [%s]", name, category.value)

    def set_llm_fallback(self, fallback_fn: Callable[[str], str]) -> None:
        """
        Set the LLM function used when no keyword/fuzzy match is found.

        The callable receives the raw text and should return the
        assistant's response.
        """

        self._llm_fallback = fallback_fn

    # ── Routing ──────────────────────────────────────────────

    def route(self, text: str) -> CommandResult:
        """
        Resolve *text* to a command and execute it.

        Returns a ``CommandResult`` with the outcome.
        """

        if not text or not text.strip():
            return CommandResult(
                category=CommandCategory.UNKNOWN,
                action="empty",
                response="I didn't hear anything. Could you repeat that?",
                success=False,
            )

        cleaned = text.strip()
        lower = cleaned.lower()

        # ── 1. Exact keyword prefix match ────────────────────
        matched_cmd = self._match_keyword(lower)

        if matched_cmd:
            return self._execute(matched_cmd, cleaned)

        # ── 2. Fuzzy match ───────────────────────────────────
        matched_cmd = self._match_fuzzy(lower)

        if matched_cmd:
            return self._execute(matched_cmd, cleaned)

        # ── 3. LLM fallback ──────────────────────────────────
        if self._llm_fallback:
            return self._llm_route(cleaned)

        # ── Nothing matched ──────────────────────────────────
        logger.info("No match for: %s", cleaned)

        return CommandResult(
            category=CommandCategory.UNKNOWN,
            action="unknown",
            response="I'm not sure what you mean. Could you try rephrasing that?",
            success=False,
        )

    # ── Internal matching ────────────────────────────────────

    def _match_keyword(self, lower: str) -> Optional[RegisteredCommand]:
        """Check if *lower* starts with any registered keyword."""

        # Sort by keyword length descending so longer keywords
        # match before shorter ones ("open chrome" before "open")
        for kw in sorted(self._keyword_map, key=len, reverse=True):
            if lower.startswith(kw):
                return self._keyword_map[kw]

        return None

    def _match_fuzzy(self, lower: str) -> Optional[RegisteredCommand]:
        """Try fuzzy matching against all registered keywords."""

        all_keywords = list(self._keyword_map.keys())

        # Extract the first 3–4 words as the likely command portion
        words = lower.split()
        command_portion = " ".join(words[:4])

        matches = fuzzy_match(
            command_portion,
            all_keywords,
            threshold=75,  # higher threshold for fuzzy to avoid false positives
            limit=1,
        )

        if matches:
            best, score = matches[0]
            logger.info(
                "Fuzzy matched '%s' → '%s' (score: %d)",
                command_portion, best, score,
            )
            return self._keyword_map.get(best)

        return None

    def _execute(
        self,
        cmd: RegisteredCommand,
        original_text: str,
    ) -> CommandResult:
        """Execute a matched command and return the result."""

        logger.info(
            "Executing [%s] %s", cmd.category.value, cmd.name
        )

        try:
            if cmd.extract_args:
                arg = extract_target(original_text, cmd.keywords)
                response = cmd.handler(arg) if arg else cmd.handler()
            else:
                response = cmd.handler()

            return CommandResult(
                category=cmd.category,
                action=cmd.name,
                response=response or "Done.",
                success=True,
            )

        except Exception as exc:
            logger.exception("Command failed: %s", cmd.name)

            return CommandResult(
                category=cmd.category,
                action=cmd.name,
                response=f"Sorry, that failed: {exc}",
                success=False,
            )

    def _llm_route(self, text: str) -> CommandResult:
        """Forward to LLM for a conversational response."""

        logger.info("Routing to LLM: %s", text[:80])

        try:
            response = self._llm_fallback(text)

            return CommandResult(
                category=CommandCategory.LLM_QUERY,
                action="llm_response",
                response=response,
                success=True,
            )

        except Exception as exc:
            logger.exception("LLM fallback failed")

            return CommandResult(
                category=CommandCategory.LLM_QUERY,
                action="llm_error",
                response=f"Sorry, I couldn't process that: {exc}",
                success=False,
            )

    # ── Introspection ────────────────────────────────────────

    def get_categories(self) -> list[str]:
        """Return all registered command categories."""

        return list(
            {cmd.category.value for cmd in self._commands}
        )

    def get_commands(
        self,
        category: Optional[CommandCategory] = None,
    ) -> list[str]:
        """List registered command names, optionally filtered."""

        if category:
            return [
                cmd.name
                for cmd in self._commands
                if cmd.category == category
            ]

        return [cmd.name for cmd in self._commands]

    def __len__(self) -> int:
        return len(self._commands)

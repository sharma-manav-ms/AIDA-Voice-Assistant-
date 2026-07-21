"""
llm.py
------
Unified LLM client with Gemini (primary) and OpenAI (fallback).

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

from __future__ import annotations

from typing import Optional

from app.config.config import GEMINI_API_KEY, OPENAI_API_KEY, get_llm_provider
from app.config.settings import (
    GEMINI_MODEL,
    OPENAI_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)
from app.ai.prompts import (
    SYSTEM_PROMPT,
    CODE_EXPLAIN_TEMPLATE,
    EMAIL_WRITER_TEMPLATE,
    SUMMARIZER_TEMPLATE,
    TRANSLATOR_TEMPLATE,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class LLMClient:
    """
    Unified LLM interface.

    Supports Google Gemini and OpenAI GPT as interchangeable
    back-ends.  The provider is chosen based on which API key
    is available, with Gemini preferred.
    """

    def __init__(self, provider: Optional[str] = None) -> None:

        self.provider = provider or get_llm_provider()

        if self.provider == "gemini":
            self._init_gemini()
        else:
            self._init_openai()

        logger.info("LLM initialized: %s", self.provider)

    # ── Provider init ────────────────────────────────────────

    def _init_gemini(self) -> None:
        """Initialize the Google Gemini client."""

        try:
            from google import genai

            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._model_name = GEMINI_MODEL

        except ImportError:
            raise RuntimeError(
                "google-genai package not installed. "
                "Run: pip install google-genai"
            )

    def _init_openai(self) -> None:
        """Initialize the OpenAI client."""

        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=OPENAI_API_KEY)
            self._model_name = OPENAI_MODEL

        except ImportError:
            raise RuntimeError(
                "openai package not installed. "
                "Run: pip install openai"
            )

    # ══════════════════════════════════════════════════════════
    #  Public API
    # ══════════════════════════════════════════════════════════

    def ask(
        self,
        prompt: str,
        context: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        General Q&A.

        Parameters
        ----------
        prompt : str
            The user's question.
        context : list[dict] | None
            Conversation history (list of {role, content} dicts).

        Returns
        -------
        str
            The model's response text.
        """

        messages = self._build_messages(SYSTEM_PROMPT, context, prompt)
        return self._call(messages)

    def explain_code(self, code: str, language: str = "") -> str:
        """Explain a piece of code."""

        prompt = CODE_EXPLAIN_TEMPLATE.format(
            language=language or "the",
            code=code,
        )
        return self._call(self._build_messages(SYSTEM_PROMPT, None, prompt))

    def solve_math(self, problem: str) -> str:
        """Solve a math problem step-by-step."""

        prompt = (
            f"Solve this math problem step by step, "
            f"showing your work:\n\n{problem}"
        )
        return self._call(self._build_messages(SYSTEM_PROMPT, None, prompt))

    def write_email(
        self,
        to: str = "",
        subject: str = "",
        hint: str = "",
    ) -> str:
        """Draft an email from a brief description."""

        prompt = EMAIL_WRITER_TEMPLATE.format(
            to=to or "the recipient",
            subject=subject or "the given topic",
            hint=hint or "a professional email",
        )
        return self._call(self._build_messages(SYSTEM_PROMPT, None, prompt))

    def summarize(self, text: str) -> str:
        """Summarize a block of text."""

        prompt = SUMMARIZER_TEMPLATE.format(text=text)
        return self._call(self._build_messages(SYSTEM_PROMPT, None, prompt))

    def translate(self, text: str, target_lang: str = "") -> str:
        """Translate text to a target language."""

        # try to extract target language from the text itself
        if not target_lang:
            lower = text.lower()
            for lang in ("spanish", "french", "german", "hindi",
                         "japanese", "chinese", "arabic", "korean",
                         "portuguese", "italian", "russian"):
                if lang in lower:
                    target_lang = lang
                    text = lower.replace(lang, "").strip()
                    break

        if not target_lang:
            target_lang = "English"

        prompt = TRANSLATOR_TEMPLATE.format(
            target_lang=target_lang,
            text=text,
        )
        return self._call(self._build_messages(SYSTEM_PROMPT, None, prompt))

    def brainstorm(self, topic: str) -> str:
        """Generate creative ideas on a topic."""

        prompt = (
            f"Brainstorm 5 creative and actionable ideas "
            f"about: {topic}"
        )
        return self._call(self._build_messages(SYSTEM_PROMPT, None, prompt))

    # ══════════════════════════════════════════════════════════
    #  Internal
    # ══════════════════════════════════════════════════════════

    def _build_messages(
        self,
        system: str,
        context: Optional[list[dict[str, str]]],
        user_prompt: str,
    ) -> list[dict[str, str]]:
        """Assemble the message list for the LLM call."""

        messages = [{"role": "system", "content": system}]

        if context:
            messages.extend(context)

        messages.append({"role": "user", "content": user_prompt})

        return messages

    def _call(self, messages: list[dict[str, str]]) -> str:
        """Dispatch to the active provider."""

        if self.provider == "gemini":
            return self._call_gemini(messages)

        return self._call_openai(messages)

    def _call_gemini(self, messages: list[dict[str, str]]) -> str:
        """Call Google Gemini API."""

        try:
            # Build contents for Gemini from messages
            # Gemini uses 'user' and 'model' roles
            contents = []

            for msg in messages:
                role = msg["role"]

                if role == "system":
                    # Gemini doesn't have a separate system role;
                    # prepend as a user instruction
                    contents.append({
                        "role": "user",
                        "parts": [{"text": f"[System] {msg['content']}"}],
                    })
                elif role == "assistant":
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg["content"]}],
                    })
                else:
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg["content"]}],
                    })

            response = self._client.models.generate_content(
                model=self._model_name,
                contents=contents,
            )

            return response.text.strip()

        except Exception as exc:
            logger.exception("Gemini API call failed")
            return f"Sorry, the AI request failed: {exc}"

    def _call_openai(self, messages: list[dict[str, str]]) -> str:
        """Call OpenAI API."""

        try:
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=messages,
                max_tokens=LLM_MAX_TOKENS,
                temperature=LLM_TEMPERATURE,
            )

            return response.choices[0].message.content.strip()

        except Exception as exc:
            logger.exception("OpenAI API call failed")
            return f"Sorry, the AI request failed: {exc}"

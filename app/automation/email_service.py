"""
email_service.py
----------------
Email automation via SMTP/IMAP.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)

Note: The filename is email_service.py (not email.py) to avoid
shadowing the built-in ``email`` package.
"""

from __future__ import annotations

import email as email_lib
import imaplib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.config.config import (
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    validate_email_credentials,
)
from app.config.settings import SMTP_SERVER, SMTP_PORT, IMAP_SERVER, IMAP_PORT
from app.utils.logger import get_logger
from app.utils.validators import validate_email

logger = get_logger(__name__)


class EmailController:
    """
    Email management using SMTP (send) and IMAP (read).

    Designed for Gmail with App Passwords (2FA accounts).
    """

    def __init__(self) -> None:
        self._available = validate_email_credentials()

        if not self._available:
            logger.warning(
                "Email credentials not configured. "
                "Set EMAIL and EMAIL_PASSWORD in .env"
            )

    # ══════════════════════════════════════════════════════════
    #  Send
    # ══════════════════════════════════════════════════════════

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
    ) -> str:
        """
        Send an email.

        Parameters
        ----------
        to : str
            Recipient email address.
        subject : str
            Email subject line.
        body : str
            Email body text.
        """

        if not self._available:
            return "Email is not configured. Please set credentials in .env."

        if not validate_email(to):
            return f"'{to}' doesn't look like a valid email address."

        try:
            msg = MIMEMultipart()
            msg["From"] = EMAIL_ADDRESS
            msg["To"] = to
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                server.send_message(msg)

            logger.info("Email sent to %s: %s", to, subject)
            return f"Email sent to {to}."

        except smtplib.SMTPAuthenticationError:
            return (
                "Email authentication failed. "
                "Make sure you're using an App Password."
            )

        except Exception as exc:
            logger.exception("Email send failed")
            return f"Couldn't send email: {exc}"

    def send_email_interactive(self, hint: str = "") -> str:
        """
        Voice-driven email sending.

        For now, provides guidance. Full interactive mode
        requires multi-turn voice input handled by the assistant.
        """

        if not self._available:
            return "Email is not configured. Please set credentials in .env."

        return (
            "To send an email, I'll need the recipient's address, "
            "subject, and message. You can say something like: "
            "'Send email to john@example.com subject Meeting "
            "body Let's meet at 3 PM.'"
        )

    # ══════════════════════════════════════════════════════════
    #  Read
    # ══════════════════════════════════════════════════════════

    def read_unread(self, count: int = 5) -> list[dict]:
        """
        Fetch the latest unread emails.

        Returns a list of dicts with keys: from, subject, date, body_preview.
        """

        if not self._available:
            return []

        try:
            with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
                mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                mail.select("inbox")

                _, message_ids = mail.search(None, "UNSEEN")
                ids = message_ids[0].split()

                if not ids:
                    return []

                # get the latest `count` emails
                recent_ids = ids[-count:]
                results = []

                for eid in reversed(recent_ids):
                    _, msg_data = mail.fetch(eid, "(RFC822)")

                    if not msg_data or not msg_data[0]:
                        continue

                    raw = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw)

                    # extract body preview
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(
                                    decode=True
                                ).decode("utf-8", errors="replace")
                                break
                    else:
                        body = msg.get_payload(
                            decode=True
                        ).decode("utf-8", errors="replace")

                    results.append({
                        "from": msg.get("From", "Unknown"),
                        "subject": msg.get("Subject", "(no subject)"),
                        "date": msg.get("Date", ""),
                        "body_preview": body[:200].strip(),
                    })

                return results

        except Exception as exc:
            logger.exception("Failed to read emails")
            return []

    def read_unread_summary(self) -> str:
        """Return a spoken summary of unread emails."""

        if not self._available:
            return "Email is not configured. Please set credentials in .env."

        emails = self.read_unread(count=5)

        if not emails:
            return "You have no unread emails."

        count = len(emails)
        summary = f"You have {count} unread email{'s' if count > 1 else ''}. "

        for i, em in enumerate(emails[:3], 1):
            sender = em["from"].split("<")[0].strip().strip('"')
            summary += f"{i}. From {sender}: {em['subject']}. "

        return summary

    # ══════════════════════════════════════════════════════════
    #  Search
    # ══════════════════════════════════════════════════════════

    def search_inbox(self, query: str) -> list[dict]:
        """Search inbox for emails matching *query*."""

        if not self._available:
            return []

        try:
            with imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT) as mail:
                mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                mail.select("inbox")

                # IMAP SUBJECT search
                _, message_ids = mail.search(
                    None, f'(SUBJECT "{query}")'
                )
                ids = message_ids[0].split()

                results = []

                for eid in ids[-10:]:
                    _, msg_data = mail.fetch(eid, "(RFC822)")

                    if not msg_data or not msg_data[0]:
                        continue

                    raw = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw)

                    results.append({
                        "from": msg.get("From", "Unknown"),
                        "subject": msg.get("Subject", "(no subject)"),
                        "date": msg.get("Date", ""),
                    })

                return results

        except Exception as exc:
            logger.exception("Email search failed")
            return []

    def search_inbox_summary(self, query: str = "") -> str:
        """Return a spoken summary of search results."""

        if not query:
            return "What should I search for in your inbox?"

        results = self.search_inbox(query)

        if not results:
            return f"I couldn't find any emails about '{query}'."

        count = len(results)
        summary = f"I found {count} email{'s' if count > 1 else ''} about '{query}'. "

        for i, em in enumerate(results[:3], 1):
            sender = em["from"].split("<")[0].strip().strip('"')
            summary += f"{i}. From {sender}: {em['subject']}. "

        return summary

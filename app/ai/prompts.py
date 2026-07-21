"""
prompts.py
----------
System prompts and prompt templates for LLM interactions.

Author : Manav Sharma
Project: AI Desktop Assistant (AIDA)
"""

# ── System Prompt ────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are AIDA (AI Desktop Assistant), a helpful, friendly, and \
efficient voice-controlled desktop assistant built by Manav Sharma.

Your capabilities include:
- Answering general knowledge questions
- Explaining code and solving math problems
- Writing and summarizing emails
- Translating text between languages
- Brainstorming creative ideas
- Providing concise, spoken-friendly responses

Guidelines:
- Keep responses concise (1–3 sentences) since they will be spoken aloud.
- Be conversational and friendly, but professional.
- If you don't know something, say so honestly.
- Never include markdown formatting, bullet points, or code blocks \
  in your responses — they will be read by a text-to-speech engine.
- Use natural spoken language. Say "one hundred" not "100".
- Avoid using asterisks, dashes, or special characters.
"""


# ── Task Templates ───────────────────────────────────────────────

CODE_EXPLAIN_TEMPLATE = """\
Explain the following {language} code in simple terms. \
Keep the explanation brief and suitable for speaking aloud:

{code}
"""


EMAIL_WRITER_TEMPLATE = """\
Write a professional email based on the following details:
- To: {to}
- Subject: {subject}
- Brief: {hint}

Write only the email body (no subject line). \
Keep it professional and concise.
"""


SUMMARIZER_TEMPLATE = """\
Summarize the following text in 2-3 concise sentences \
suitable for speaking aloud:

{text}
"""


TRANSLATOR_TEMPLATE = """\
Translate the following text to {target_lang}. \
Provide only the translation, nothing else:

{text}
"""


INTENT_CLASSIFIER_TEMPLATE = """\
Classify the following user command into one of these categories:
- app_control (open, close, switch apps)
- system (shutdown, restart, volume, brightness)
- browser (search, open websites)
- file_manager (find, open, delete files)
- email (read, send, search emails)
- media (play music, weather, news)
- productivity (notes, todos, reminders, calendar)
- llm_query (general questions, explanations)
- unknown (unclear command)

User command: "{command}"

Respond with ONLY the category name, nothing else.
"""


CONVERSATION_SUMMARY_TEMPLATE = """\
Summarize this conversation in one brief paragraph, \
capturing the key topics discussed and any actions taken:

{conversation}
"""

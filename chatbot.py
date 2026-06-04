import os
from typing import cast, Iterable

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


SYSTEM_PROMPT = """
You are StockSage, a careful financial education assistant.

Your job:
- Explain financial concepts clearly and practically.
- Help users reason about stocks, ETFs, markets, risk, diversification, and valuation.
- Ask clarifying questions when a user's goal or risk profile is unclear.
- Be explicit when information may be outdated or when live market data is needed.
- Avoid giving personalized buy/sell/hold instructions.
- Encourage users to verify important decisions with a qualified financial advisor.

When discussing investments, include relevant risks and assumptions.
""".strip()


class ChatbotConfigurationError(RuntimeError):
    """Raised when required chatbot configuration is missing."""


def build_messages(chat_history: Iterable[dict[str, str]]) -> list[dict[str, str]]:
    messages = []
    seen_user_message = False

    for item in chat_history:
        role = item.get("role")
        content = item.get("content")

        if not content:
            continue

        if role == "user":
            seen_user_message = True
            messages.append({"role": "user", "content": content})
        elif role == "assistant" and seen_user_message:
            messages.append({"role": "model", "content": content})

    return messages


class FinancialChatbot:
    def __init__(self, temperature: float = 0.3) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ChatbotConfigurationError(
                "Missing `GEMINI_API_KEY`. Copy `.env.example` to `.env` and add your key."
            )

        self.client = genai.Client(api_key=api_key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.temperature = temperature

    def reply(self, messages: list[dict[str, str]]) -> str:
        contents = cast(
            types.ContentListUnionDict,
            [
                types.Content(
                    role=message["role"],
                    parts=[types.Part.from_text(text=message["content"])],
                )
                for message in messages
            ],
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=self.temperature,
            ),
        )

        answer = response.text
        if not answer:
            return "I received an empty response. Please try rephrasing your question."

        return answer.strip()

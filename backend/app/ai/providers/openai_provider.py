from typing import Any

from backend.app.ai.providers.local import LocalProvider


class OpenAIProvider(LocalProvider):
    provider_name = "openai"

    def __init__(self, api_key: str, model_name: str) -> None:
        self.api_key = api_key
        self.model_name = model_name

    def _call(self, system: str, user: str) -> str:
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key)
            response = client.responses.create(
                model=self.model_name,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.2,
                max_output_tokens=250,
            )
            return response.output_text.strip()
        except Exception:
            return ""

    def generate_reply(self, context: str, customer_message: str, intent: str) -> str:
        if not context:
            return super().generate_reply(context, customer_message, intent)
        generated = self._call(
            "You draft concise e-commerce support replies grounded only in provided context.",
            (
                f"Intent: {intent}\n"
                f"Customer message: {customer_message}\n"
                f"Verified context:\n{context}\n"
                "Do not add facts not present in context."
            ),
        )
        return generated or super().generate_reply(context, customer_message, intent)

    def summarize_ticket(self, ticket_messages: list[str]) -> str:
        generated = self._call(
            "Summarize support tickets for managers in 2-3 concise bullets.",
            "\n".join(ticket_messages),
        )
        return generated or super().summarize_ticket(ticket_messages)

    def draft_manager_note(self, ticket: dict[str, Any]) -> str:
        generated = self._call(
            "Write a short manager note for an escalated e-commerce support ticket.",
            str(ticket),
        )
        return generated or super().draft_manager_note(ticket)

    def format_report_summary(self, metrics: dict[str, Any]) -> str:
        generated = self._call(
            "Format support analytics into a short manager Telegram report.",
            str(metrics),
        )
        return generated or super().format_report_summary(metrics)

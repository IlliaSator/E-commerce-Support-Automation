from abc import ABC, abstractmethod
from typing import Any


class AIProvider(ABC):
    provider_name: str
    model_name: str

    @abstractmethod
    def generate_reply(self, context: str, customer_message: str, intent: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def summarize_ticket(self, ticket_messages: list[str]) -> str:
        raise NotImplementedError

    @abstractmethod
    def classify_sentiment(self, message: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def draft_manager_note(self, ticket: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    def format_report_summary(self, metrics: dict[str, Any]) -> str:
        raise NotImplementedError

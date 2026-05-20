from __future__ import annotations

import asyncio
import logging

import httpx
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.app.admin import is_admin
from bot.app.client import BackendClient
from bot.app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
dp = Dispatcher()
backend = BackendClient(settings)


def _format_support_response(data: dict) -> str:
    lines = [data.get("reply_text", "Support request processed.")]
    if data.get("ticket_id"):
        lines.append(f"Ticket ID: #{data['ticket_id']}")
    if data.get("escalation"):
        lines.append("A human manager was notified.")
    return "\n".join(lines)


def _admin_required(message: Message) -> bool:
    return bool(message.chat and is_admin(message.chat.id, settings))


@dp.message(Command("start"))
async def start(message: Message) -> None:
    await message.answer(
        "Hi! I am TechGear Store support assistant. Send a question, or use /order 10042."
    )


@dp.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "Customer commands: /order <order_id>, /ticket <ticket_id>, /faq.\n"
        "Managers: /open_tickets, /ticket <ticket_id>, /resolve <ticket_id>, /sla, /report."
    )


@dp.message(Command("faq"))
async def faq(message: Message) -> None:
    await message.answer(
        "I can answer delivery, payment, warranty, order tracking, product availability, returns, and complaints."
    )


@dp.message(Command("order"))
async def order(message: Message, command: CommandObject) -> None:
    order_id = (command.args or "").strip()
    text = f"Where is my order {order_id}?" if order_id else "Where is my order?"
    await forward_to_backend(message, override_text=text)


@dp.message(Command("open_tickets"))
async def open_tickets(message: Message) -> None:
    if not _admin_required(message):
        await message.answer("This command is available only to managers.")
        return
    try:
        tickets = await backend.admin_get("/tickets/open")
    except httpx.HTTPError:
        await message.answer("Backend is unavailable. Please try again later.")
        return
    if not tickets:
        await message.answer("No open tickets.")
        return
    lines = [
        f"#{t['id']} {t['priority']} {t['intent']} {t['status']} SLA: {t.get('sla_due_at')}"
        for t in tickets[:10]
    ]
    await message.answer("\n".join(lines))


@dp.message(Command("ticket"))
async def ticket(message: Message, command: CommandObject) -> None:
    ticket_id = (command.args or "").strip()
    if not ticket_id:
        await message.answer("Usage: /ticket <ticket_id>")
        return
    if not _admin_required(message):
        await message.answer(f"Ticket #{ticket_id} is being reviewed by support.")
        return
    try:
        data = await backend.admin_get(f"/tickets/{ticket_id}")
    except httpx.HTTPStatusError as exc:
        await message.answer(f"Could not load ticket: {exc.response.status_code}")
        return
    except httpx.HTTPError:
        await message.answer("Backend is unavailable. Please try again later.")
        return
    await message.answer(
        f"Ticket #{data['id']}\n"
        f"Status: {data['status']}\nPriority: {data['priority']}\nIntent: {data['intent']}\n"
        f"Message: {data['message_text']}\nSuggested reply: {data.get('suggested_reply') or '-'}"
    )


@dp.message(Command("resolve"))
async def resolve(message: Message, command: CommandObject) -> None:
    if not _admin_required(message):
        await message.answer("This command is available only to managers.")
        return
    ticket_id = (command.args or "").strip()
    if not ticket_id:
        await message.answer("Usage: /resolve <ticket_id>")
        return
    try:
        data = await backend.admin_post(
            f"/tickets/{ticket_id}/resolve",
            {"final_reply": "Resolved by manager from Telegram.", "ai_suggestion_status": "edited"},
        )
    except httpx.HTTPError:
        await message.answer("Backend is unavailable or the ticket does not exist.")
        return
    await message.answer(f"Ticket #{data['id']} resolved.")


@dp.message(Command("sla"))
async def sla(message: Message) -> None:
    if not _admin_required(message):
        await message.answer("This command is available only to managers.")
        return
    try:
        data = await backend.admin_get("/analytics/sla-breaches")
    except httpx.HTTPError:
        await message.answer("Backend is unavailable. Please try again later.")
        return
    if data["count"] == 0:
        await message.answer("No SLA breaches.")
    else:
        await message.answer(f"SLA breaches: {data['count']}")


@dp.message(Command("report"))
async def report(message: Message) -> None:
    if not _admin_required(message):
        await message.answer("This command is available only to managers.")
        return
    try:
        data = await backend.admin_get("/analytics/daily")
    except httpx.HTTPError:
        await message.answer("Backend is unavailable. Please try again later.")
        return
    await message.answer(
        f"Daily report\n"
        f"Messages: {data['total_messages']}\n"
        f"Auto-resolved: {data['auto_resolved_messages']}\n"
        f"Tickets: {data['created_tickets']} ({data['open_tickets']} open)\n"
        f"SLA breaches: {data['sla_breaches']}"
    )


@dp.message(F.text)
async def forward_to_backend(message: Message, override_text: str | None = None) -> None:
    text = override_text or message.text or ""
    try:
        data = await backend.support_message(
            customer_id=str(message.from_user.id if message.from_user else message.chat.id),
            chat_id=message.chat.id,
            username=message.from_user.username if message.from_user else None,
            message_text=text,
        )
        await message.answer(_format_support_response(data))
    except httpx.HTTPError:
        await message.answer("Support backend is unavailable. Please try again later.")


async def main() -> None:
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN is missing. Bot is running in documented mock/sleep mode.")
        await asyncio.Event().wait()
        return
    bot = Bot(settings.telegram_bot_token)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

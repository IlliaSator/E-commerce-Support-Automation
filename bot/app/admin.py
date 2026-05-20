from bot.app.config import BotSettings


def is_admin(chat_id: int, settings: BotSettings) -> bool:
    return chat_id in settings.manager_ids

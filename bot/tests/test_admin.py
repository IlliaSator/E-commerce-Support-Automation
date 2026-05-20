from bot.app.admin import is_admin
from bot.app.config import BotSettings


def test_admin_authorization_matches_manager_chat_ids():
    settings = BotSettings(manager_chat_ids="100,200")
    assert is_admin(100, settings) is True
    assert is_admin(300, settings) is False

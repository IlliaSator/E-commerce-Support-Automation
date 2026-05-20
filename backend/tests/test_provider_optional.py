from backend.app.ai.providers.factory import get_provider


def test_openai_provider_is_optional_by_default():
    provider = get_provider()
    assert provider.provider_name == "local"
    assert provider.generate_reply("", "hello", "unknown")

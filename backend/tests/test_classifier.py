from backend.app.ai.classifier import classify_message, extract_order_id


def test_extract_order_id_from_english_message():
    assert extract_order_id("Where is my order 10042?") == "10042"


def test_extract_order_id_from_russian_message():
    assert extract_order_id("Где мой заказ 10042?") == "10042"


def test_damaged_item_classifies_as_complaint():
    result = classify_message("My order arrived broken")
    assert result.intent == "complaint"
    assert result.confidence >= 0.75


def test_refund_request_classifies_as_return_refund_not_auto_decision():
    result = classify_message("I need a refund")
    assert result.intent == "return_refund"
    assert result.confidence >= 0.75


def test_human_manager_request_classifies_as_human_agent():
    result = classify_message("I need a human manager")
    assert result.intent == "human_agent"

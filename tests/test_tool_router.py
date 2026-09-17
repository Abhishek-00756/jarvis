"""Focused tests for dynamic tool discovery v1."""

from agent.tool_router import select_relevant_tools, validate_registry


def names(tools):
    return {tool.name for tool in tools}


def test_music_query_is_scoped():
    selected = select_relevant_tools("pause the music")
    assert names(selected) == {
        "media_play",
        "media_pause",
        "media_next_track",
        "media_previous_track",
        "media_current_track",
    }


def test_ambiguous_query_falls_back_to_full_registry():
    selected = select_relevant_tools("what's the weather")
    registry = validate_registry()
    assert len(selected) == registry["registry_count"]


def test_reel_whatsapp_request_keeps_context_browser_and_messaging():
    selected = names(select_relevant_tools("send this reel to Rahul on WhatsApp"))
    assert "get_current_context" in selected
    assert "get_active_browser_tab" in selected
    assert "whatsapp_send_message" in selected
    assert "browser_get_current_url" in selected
    assert "browser_get_text" in selected


def test_calendar_query_is_scoped_to_calendar_tools():
    selected = names(select_relevant_tools("what meetings are on my calendar tomorrow"))
    assert "get_calendar_events_today" in selected
    assert "get_calendar_events_range" in selected
    assert "find_event" in selected
    assert "send_message" not in selected


def test_registry_has_no_missing_or_phantom_category_entries():
    result = validate_registry()
    assert result["missing"] == []
    assert result["phantom"] == []
    assert result["registry_unique_count"] == result["registry_count"]
    assert result["categorized_unique_count"] == result["categorized_count"]

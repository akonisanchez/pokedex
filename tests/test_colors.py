from app import _text_color_for_bg


def test_text_color_for_bright_background_is_dark_text():
    # Electric yellow should result in dark text
    assert _text_color_for_bg("#F7D02C") == "#111111"


def test_text_color_for_dark_background_is_white_text():
    # Ghost purple should result in white text
    assert _text_color_for_bg("#735797") == "#ffffff"
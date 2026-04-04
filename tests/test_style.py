from prose_hygiene.style import rewrite_document_text, rewrite_line


def test_fenced_code_block_is_unchanged():
    text = 'before\n```python\na = 1 — 2\n```\nafter\n'
    result = rewrite_document_text(text)
    assert 'a = 1 — 2' in result.text


def test_list_descriptor_becomes_colon():
    text = '- Inventory tab — paste from SolarWinds\n'
    result = rewrite_document_text(text)
    assert '- Inventory tab: paste from SolarWinds\n' == result.text


def test_transition_becomes_comma():
    text = 'It works — but only after restart.\n'
    result = rewrite_document_text(text)
    assert 'It works, but only after restart.\n' == result.text


def test_parenthetical_requires_two_words():
    text = 'He said — no — nothing.\n'
    result = rewrite_document_text(text)
    assert '(no)' not in result.text


def test_heading_comma_default_off():
    text = 'Responses Sheet, Column Reference\n'
    result = rewrite_document_text(text)
    assert result.text == text


def test_heading_comma_opt_in_on():
    text = 'Responses Sheet, Column Reference\n'
    result = rewrite_document_text(text, normalize_heading_commas=True)
    assert result.text == 'Responses Sheet: Column Reference\n'


def test_heading_style_requires_title_case_or_short_label():
    rewritten, count, strategies = rewrite_line('ordinary sentence — still going')
    assert rewritten == 'ordinary sentence, still going'
    assert count == 1
    assert strategies == {'comma': 1}


def test_heading_comma_opt_in_does_not_change_list_items():
    text = '- Responses Sheet, Column Reference\n'
    result = rewrite_document_text(text, normalize_heading_commas=True)
    assert result.text == text


def test_parenthetical_does_not_trigger_when_middle_has_terminal_punctuation():
    rewritten, count, _ = rewrite_line('We changed it — which is unusual. — yesterday.')
    assert count == 2
    assert '(which is unusual.)' not in rewritten


def test_parenthetical_does_not_trigger_when_middle_is_too_long():
    rewritten, count, _ = rewrite_line(
        'We changed it — which is much more verbose than the heuristic allows in this specific edge case today — yesterday.'
    )
    assert count == 2
    assert '(' not in rewritten

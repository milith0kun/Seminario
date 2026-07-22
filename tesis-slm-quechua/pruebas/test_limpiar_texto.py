from src.ingesta.limpiar_texto import clean_text, estimate_tokens


def test_clean_text_spaces():
    assert clean_text("hola   mundo\n\n\nchao") == "hola mundo\n\nchao"


def test_estimate_tokens():
    assert estimate_tokens("uno dos tres") >= 3

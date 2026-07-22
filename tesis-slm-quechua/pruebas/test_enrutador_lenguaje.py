from src.inferencia.enrutador_lenguaje import detect_language


def test_detect_es():
    assert detect_language("Que es la fotosintesis?") == "es"


def test_detect_qu():
    assert detect_language("Imaynata yachay wasi kan?") == "qu_collao"


def test_detect_mixed():
    assert detect_language("Como se dice agua yaku en la clase?") in {"mixed_es_qu", "es", "qu_collao"}

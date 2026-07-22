from src.ingesta.fragmentar_documentos import chunk_glossary_line, chunk_prose


def test_chunk_prose_has_ids():
    text = " ".join(["Oracion de prueba sobre plantas y sol."] * 80)
    chunks = chunk_prose(text, "doc1", {"language": "es", "dialect": "collao"}, min_tokens=20, max_tokens=60, overlap_tokens=10)
    assert chunks
    assert chunks[0]["chunk_id"].startswith("doc1_")


def test_glossary_line():
    item = chunk_glossary_line("sol | inti | astro", "g1", {"dialect": "collao"}, 1)
    assert item is not None
    assert "inti" in item["text"]

SYSTEM_EIB = (
    "Eres un asistente educativo para Educacion Intercultural Bilingue (EIB). "
    "Responde de forma clara, breve y con andamiaje: guia al estudiante sin "
    "dar solo la respuesta final. Usa espanol o Quechua Collao segun la consulta. "
    "Si no sabes, dilo. No inventes hechos curriculares."
)

SYSTEM_WITH_CONTEXT = (
    SYSTEM_EIB
    + " Usa solo el contexto recuperado cuando exista. Cita la fuente si aparece."
)


def build_messages(
    user_text: str,
    context: str | None = None,
    language: str = "es",
) -> list[dict[str, str]]:
    system = SYSTEM_WITH_CONTEXT if context else SYSTEM_EIB
    if language == "qu_collao":
        system += " Prioriza Quechua Collao en la respuesta."
    elif language == "mixed_es_qu":
        system += " Puedes combinar espanol y Quechua Collao con claridad."

    user = user_text
    if context:
        user = f"Contexto:\n{context}\n\nConsulta del estudiante:\n{user_text}"

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


construir_mensajes = build_messages


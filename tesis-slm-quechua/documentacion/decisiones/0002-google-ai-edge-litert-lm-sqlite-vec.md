# Decision 0002: Adopción del Ecosistema Google AI Edge (LiteRT-LM + sqlite-vec) para Despliegue Móvil Bilingüe

**Estado:** Aprobado / Propuesto para Evaluación Móvil

## Contexto y Desafío
El prototipo inicial de la tesis (ADR 0001) estableció `Qwen2.5-3B-Instruct` con `llama.cpp` (GGUF Q4_K_M) y búsqueda vectorial planificada en `FAISS`. Si bien esta combinación es excelente para pruebas de escritorio en Windows/Linux, el despliegue en teléfonos inteligentes reales para Educación Intercultural Bilingüe (EIB) en zonas rurales del Perú impone restricciones extremas de RAM (1.3–2.0 GB utilizables para IA) y latencia.

## Decisión
Incorporar como arquitectura de referencia móvil de alto rendimiento el stack de **Google AI Edge Gallery**:
1. **Motor de Inferencia:** Migrar/extender desde `llama.cpp` hacia **LiteRT-LM** (Lite Runtime Language Model).
2. **Formato de Contenedor:** Empaquetar modelos convertidos con `ai-edge-torch` y cuantizados (`ai-edge-quantizer`) bajo el estándar `.litertlm` (que empaqueta pesos, tokenizador SentencePiece y metadatos TOML).
3. **Recuperación Vectorial:** Reemplazar la dependencia pesada de FAISS por **`sqlite-vec`** (extensión de C puro para SQLite con aceleración SIMD ARM NEON y tablas virtuales `vec0_vtab`).
4. **Andamiaje Pedagógico:** Implementar **Agent Skills** (manifiestos `SKILL.md` + Function Calling determinista en JS/Dart) para forzar el método socrático/constructivista sin alucinaciones.
5. **Framework de App Móvil:** Abstraer el despliegue nativo multiplataforma mediante **Flutter** + **`flutter_gemma`** (`flutter_gemma_rag_sqlite`), configurando `AndroidManifest.xml` con `libOpenCL.so` y `libvndksupport.so`.

## Razones e Impacto Medible
- **Rendimiento:** Decodificación acelerada a 51–55 tokens/seg (vs ~37–39 en llama.cpp móvil) y picos de RAM reducidos a 1.3–2.0 GB gracias a `mmap` y Multi-Token Prediction (MTP).
- **Morfología Quechua:** La inyección estricta del tokenizador en `.litertlm` previene la fragmentación caótica de sufijos del Quechua Collao.
- **Portabilidad RAG:** Base de datos vectorial precompilada e ingerida *offline* como un archivo estático SQLite dentro del APK.
- **Desvinculación Total de la Nube:** Eliminación de telemetría (Firebase/OAuth) y operación 100% autónoma.

## Documentación Completa y Repositorios
- Informe técnico exhaustivo: [ARQUITECTURA_GOOGLE_AI_EDGE_RAG_QUECHUA.md](file:///d:/Proyectos/Seminario/tesis-slm-quechua/documentacion/ARQUITECTURA_GOOGLE_AI_EDGE_RAG_QUECHUA.md)
- [Google AI Edge Gallery](https://github.com/google-ai-edge/gallery)
- [LiteRT-LM Engine & Builder](https://github.com/google-ai-edge/LiteRT-LM)
- [AI Edge Quantizer](https://github.com/google-ai-edge/ai-edge-quantizer)
- [sqlite-vec Vector Store](https://github.com/asg017/sqlite-vec)
- [flutter_gemma Binding](https://github.com/DenisovAV/flutter_gemma)


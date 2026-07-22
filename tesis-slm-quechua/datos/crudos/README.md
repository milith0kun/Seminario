# Fuentes crudas (`data/raw`)

Coloca aqui los documentos originales del proyecto.

## Estructura sugerida

```text
data/raw/
  minedu/
  glosarios/
  corpus/
  diccionarios/
  sample/
```

## Reglas

1. Toda fuente debe registrarse en `data/manifest.csv`.
2. Etiqueta el dialecto: `collao`, `chanka`, `cusco` o `unknown`.
3. No mezclar Chanka con Collao sin etiqueta explicita.
4. Preferir materiales EIB de Comunicacion y Ciencia y Tecnologia (3-6 grado).
5. Si no esta en el manifiesto, no entra al RAG ni al entrenamiento.

## Formatos iniciales soportados por el pipeline

- `.txt` (listo)
- PDF/DOCX/XLSX se agregaran despues; por ahora exporta a texto.

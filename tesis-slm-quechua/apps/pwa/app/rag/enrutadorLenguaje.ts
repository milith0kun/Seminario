// Puerto literal de src/inferencia/enrutador_lenguaje.py

export type IdiomaDetectado = 'es' | 'qu_collao' | 'mixed_es_qu' | 'unknown';

const QU_MARKERS = new Set([
  'imaynata',
  'ima',
  'mayqin',
  'allin',
  'yachay',
  'yachachiq',
  'wawa',
  'runa',
  'pacha',
  'yaku',
  'inti',
  'waspi',
  'kay',
  'chay',
  'ñuqa',
  'nuqa',
  'qam',
  'pay',
  'noqanchis',
  'rimay',
  'qillqay',
  "t'ikray",
  'kawsay',
  'pukllay',
]);

const ES_MARKERS = new Set([
  'que',
  'es',
  'la',
  'el',
  'de',
  'para',
  'como',
  'porque',
  'una',
  'los',
]);

const QU_SUFFIXES = ['chu', 'paq', 'kuna', 'ykuna'];

export function detectLanguage(text: string): IdiomaDetectado {
  const tokens = text.toLowerCase().match(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+/g);
  if (!tokens || tokens.length === 0) {
    return 'unknown';
  }

  let quHits = 0;
  let esHits = 0;
  for (const t of tokens) {
    if (QU_MARKERS.has(t) || QU_SUFFIXES.some((suf) => t.endsWith(suf))) {
      quHits += 1;
    }
    if (ES_MARKERS.has(t)) {
      esHits += 1;
    }
  }

  if (quHits >= 2 && esHits >= 2) {
    return 'mixed_es_qu';
  }
  if (quHits >= 2 && quHits > esHits) {
    return 'qu_collao';
  }
  if (esHits >= 1 || quHits === 0) {
    return 'es';
  }
  if (quHits >= 1) {
    return 'qu_collao';
  }
  return 'unknown';
}

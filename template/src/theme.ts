import { loadFont as loadArchivo } from "@remotion/google-fonts/Archivo";
import { loadFont as loadInstrument } from "@remotion/google-fonts/InstrumentSans";

export const { fontFamily: TITLE } = loadArchivo("normal", { weights: ["800", "900"], subsets: ["latin"] });
export const { fontFamily: BODY } = loadInstrument("normal", { weights: ["600"], subsets: ["latin"] });

export const C = {
  bg: "#0B0A10",
  card: "rgba(21,19,28,0.92)",
  cardSolid: "#15131C",
  line: "rgba(255,255,255,0.09)",
  text: "#F4F2F8",
  muted: "#9C97AB",
  lime: "#D7F25A",
  violet: "#A77BFF",
  red: "#FF6B6B",
};

// ---------- marca (lo completa la skill en la entrevista inicial) ----------
// lime = color de acento principal · violet = acento secundario (los nombres quedan por compatibilidad).
export const MARCA = {
  handle: "@TU_USUARIO", // aparece abajo a la derecha en los videos horizontales
  ctaPalabra: "VIDEO", // reels: "Comenta VIDEO…"
  ctaTexto: "y te envío el video completo",
};

// ---------- estilo PRO (variedad visual; ver references/efectos-pro.md) ----------
export type Entrada =
  | "subir" | "bajar" | "izquierda" | "derecha" | "escala" | "desenfoque" | "revelar" | "giro" | "caer" | "elastico";
export type TipoTransicion =
  | "flash" | "latigo" | "zoom" | "glitch" | "luz" | "barrido" | "sacudida" | "desenfoque";
export type EstiloSubs = "caja" | "contorno" | "pop" | "karaoke" | "marcador" | "minimal" | "neon";
export type TipoFondo = "aurora" | "grilla" | "degradado" | "liso" | "particulas" | "ondas";

export const ESTILO = {
  /** cómo se ven los subtítulos (todas las opciones en efectos-pro.md) */
  subtitulos: "caja" as EstiloSubs,
  mayusculas: false,
  /** entradas de tarjetas: si una tarjeta no trae `anim`, elige una de esta lista (variada y siempre igual en cada render) */
  animaciones: ["subir", "izquierda", "escala", "desenfoque", "revelar", "giro"] as Entrada[],
  /** transiciones que rotan cuando una transición es "auto" */
  transiciones: ["latigo", "zoom", "flash", "barrido", "luz"] as TipoTransicion[],
  /** fondo detrás de la cámara cuando está en recuadro / pantalla dividida */
  fondo: "aurora" as TipoFondo,
  /** look de cine encima de todo: viñeta y grano (0 = nada, 1 = fuerte); barras = formato cine 2.39:1 */
  look: { vineta: 0.3, grano: 0.18, barras: false },
  /** volumen general de los efectos de sonido (1 = normal) */
  sonido: 1,
};

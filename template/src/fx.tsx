// Efectos PRO compartidos por videos largos y reels (el mismo archivo está en template/ y template-reel/).
// NO editar por video: se configuran desde theme.ts → ESTILO y se usan en video.tsx.
// Catálogo y reglas de uso: references/efectos-pro.md
import React from "react";
import { AbsoluteFill, Easing, interpolate, random, useCurrentFrame, useVideoConfig } from "remotion";
import { C, TITLE, BODY, ESTILO, Entrada, TipoTransicion, EstiloSubs, TipoFondo } from "./theme";
import { BEATS } from "./beats";

const useT = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return f / fps;
};
const CL = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const EASE = {
  suave: Easing.bezier(0.22, 1, 0.36, 1),
  rebote: Easing.out(Easing.back(1.8)),
  elastico: Easing.out(Easing.elastic(1.1)),
  seco: Easing.bezier(0.7, 0, 0.2, 1),
  lento: Easing.inOut(Easing.cubic),
};
/** 0→1 entre `at` y `at+dur` con la curva elegida */
export const p01 = (t: number, at: number, dur: number, easing = EASE.suave) =>
  interpolate(t, [at, at + dur], [0, 1], { ...CL, easing });
const pick = <T,>(list: readonly T[], seed: string): T => list[Math.floor(random(seed) * list.length) % list.length];
const bell = (u: number) => Math.sin(Math.PI * Math.min(1, Math.max(0, u)));

// ======================= entradas de tarjetas =======================
const TODAS: Entrada[] = ["subir", "bajar", "izquierda", "derecha", "escala", "desenfoque", "revelar", "giro", "caer", "elastico"];

/** Entrada por defecto de una tarjeta (variada, determinista: siempre la misma para el mismo `from`). */
export const elegirEntrada = (from: number): Entrada =>
  pick(ESTILO.animaciones.length ? ESTILO.animaciones : TODAS, `entrada-${Math.round(from * 100)}`);

/** Estilo (opacity/transform/filter/clip) de una pieza que entra en `from` y sale en `to`. */
export const estiloEntrada = (tipo: Entrada, t: number, from: number, to: number): React.CSSProperties => {
  const out = p01(t, to, 0.3, EASE.lento);
  const fade = (d = 0.35) => p01(t, from, d);
  switch (tipo) {
    case "caer": {
      const i = p01(t, from, 0.6, EASE.rebote);
      return { opacity: fade(0.2) * (1 - out), transform: `translateY(${(1 - i) * -160 + out * 40}px)` };
    }
    case "elastico": {
      const i = p01(t, from, 0.8, EASE.elastico);
      return { opacity: fade(0.15) * (1 - out), transform: `scale(${0.6 + 0.4 * i - out * 0.08})` };
    }
    case "bajar": {
      const i = p01(t, from, 0.5);
      return { opacity: i * (1 - out), transform: `translateY(${(1 - i) * -60 + out * 30}px)` };
    }
    case "izquierda": {
      const i = p01(t, from, 0.55);
      return { opacity: i * (1 - out), transform: `translateX(${(1 - i) * -140 - out * 60}px)` };
    }
    case "derecha": {
      const i = p01(t, from, 0.55);
      return { opacity: i * (1 - out), transform: `translateX(${(1 - i) * 140 + out * 60}px)` };
    }
    case "escala": {
      const i = p01(t, from, 0.5, EASE.rebote);
      return { opacity: fade(0.25) * (1 - out), transform: `scale(${0.82 + 0.18 * i + out * 0.06})` };
    }
    case "desenfoque": {
      const i = p01(t, from, 0.55);
      return { opacity: i * (1 - out), filter: `blur(${(1 - i) * 18 + out * 12}px)`, transform: `scale(${1.06 - 0.06 * i})` };
    }
    case "revelar": {
      const i = p01(t, from, 0.6, EASE.seco);
      return { opacity: 1 - out, clipPath: `inset(0 ${(1 - i) * 100}% 0 0 round 36px)`, transform: `translateX(${(1 - i) * -20}px)` };
    }
    case "giro": {
      const i = p01(t, from, 0.6);
      return {
        opacity: i * (1 - out),
        transform: `perspective(1400px) rotateX(${(1 - i) * -40 + out * 20}deg) translateY(${(1 - i) * 50}px)`,
        transformOrigin: "50% 0%",
      };
    }
    default: {
      const i = p01(t, from, 0.5);
      return { opacity: i * (1 - out), transform: `translateY(${(1 - i) * 60 + out * -30}px) scale(${0.96 + 0.04 * i})` };
    }
  }
};

// ======================= transiciones =======================
export type Transicion = { at: number; tipo?: TipoTransicion | "auto"; dur?: number; color?: string };
type TrR = { at: number; tipo: TipoTransicion; dur: number; color?: string; i: number };
const DUR: Record<TipoTransicion, number> = {
  flash: 0.35, latigo: 0.45, zoom: 0.5, glitch: 0.4, luz: 1.0, barrido: 0.6, sacudida: 0.45, desenfoque: 0.5,
};

/** Resuelve las "auto" rotando ESTILO.transiciones sin repetir la anterior. */
export const resolverTransiciones = (list: Transicion[]): TrR[] => {
  const pool = ESTILO.transiciones.length ? ESTILO.transiciones : (["latigo", "zoom", "flash"] as TipoTransicion[]);
  let prev: TipoTransicion | null = null;
  return [...list]
    .sort((a, b) => a.at - b.at)
    .map((tr, i) => {
      let tipo: TipoTransicion;
      if (!tr.tipo || tr.tipo === "auto") {
        tipo = pick(pool, `tr-${i}-${Math.round(tr.at * 100)}`);
        if (tipo === prev && pool.length > 1) tipo = pool[(pool.indexOf(tipo) + 1) % pool.length];
      } else tipo = tr.tipo;
      prev = tipo;
      return { at: tr.at, tipo, dur: tr.dur ?? DUR[tipo], color: tr.color, i };
    });
};

/** Una transición "auto" en cada tiempo de la lista (p. ej. los cambios de encuadre). `cada` = 2 → una sí, una no. */
export const autoTransiciones = (times: number[], cada = 1): Transicion[] =>
  times.filter((_, i) => i % cada === 0).map((at) => ({ at, tipo: "auto" as const }));

/** Efecto de sonido que acompaña a cada transición (sumarlo a la lista SFX). */
export const sfxDeTransiciones = (list: Transicion[]): { at: number; f: SfxName; v?: number }[] => {
  const SON: Record<TipoTransicion, [SfxName, number]> = {
    latigo: ["swoosh", 0.8], zoom: ["whoosh", 0.8], flash: ["impacto", 0.6], glitch: ["glitch", 0.6],
    luz: ["brillo", 0.5], barrido: ["whoosh", 0.8], sacudida: ["boom", 0.5], desenfoque: ["swoosh", 0.6],
  };
  return resolverTransiciones(list).map((tr) => ({ at: Math.max(0, tr.at - tr.dur * 0.4), f: SON[tr.tipo][0], v: SON[tr.tipo][1] }));
};

const activa = (list: TrR[], t: number) => list.find((tr) => t >= tr.at - tr.dur / 2 && t <= tr.at + tr.dur / 2);

/**
 * Envuelve las capas visuales (fondo, cámara, tarjetas) y les aplica las transiciones.
 * Los subtítulos y la marca van FUERA para que se lean siempre.
 */
export const ConTransiciones: React.FC<{ list: Transicion[]; children: React.ReactNode }> = ({ list, children }) => {
  const t = useT();
  const f = useCurrentFrame();
  const tr = activa(resolverTransiciones(list), t);
  let style: React.CSSProperties = {};
  let overlay: React.ReactNode = null;
  if (tr) {
    const u = (t - (tr.at - tr.dur / 2)) / tr.dur;
    const b = bell(u);
    const dir = tr.i % 2 ? -1 : 1;
    const jit = (k: string, a: number) => (random(`${k}-${f}`) - 0.5) * 2 * a;
    switch (tr.tipo) {
      case "latigo":
        style = { transform: `translateX(${dir * b * 240}px) skewX(${dir * b * -6}deg)`, filter: `blur(${b * 18}px)` };
        break;
      case "zoom":
        style = { transform: `scale(${1 + b * 0.28})`, filter: `blur(${b * 10}px)` };
        break;
      case "sacudida": {
        const a = 26 * (1 - u);
        style = { transform: `translate(${jit("sx", a)}px, ${jit("sy", a)}px) rotate(${jit("sr", a / 20)}deg)` };
        break;
      }
      case "desenfoque":
        style = { filter: `blur(${b * 24}px) brightness(${1 + b * 0.15})` };
        break;
      case "glitch":
        style = b > 0.15 ? { transform: `translateX(${jit("gx", 30 * b)}px)`, filter: `hue-rotate(${jit("gh", 90)}deg) saturate(1.8)` } : {};
        overlay = <GlitchBars b={b} f={f} />;
        break;
      case "flash":
        overlay = <AbsoluteFill style={{ background: tr.color ?? "#fff", opacity: Math.pow(b, 1.5) * 0.85 }} />;
        break;
      case "luz":
        overlay = <LightLeak u={u} b={b} />;
        break;
      case "barrido":
        overlay = <Barrido u={u} color={tr.color} />;
        break;
    }
  }
  return (
    <AbsoluteFill>
      <AbsoluteFill style={style}>{children}</AbsoluteFill>
      {overlay}
    </AbsoluteFill>
  );
};

const GlitchBars: React.FC<{ b: number; f: number }> = ({ b, f }) => (
  <AbsoluteFill style={{ mixBlendMode: "screen", opacity: b }}>
    {Array.from({ length: 7 }).map((_, i) => {
      const y = random(`gb-y-${i}-${f}`) * 100;
      const h = 1 + random(`gb-h-${i}-${f}`) * 7;
      const col = [C.lime, C.violet, C.red][i % 3];
      return (
        <div key={i} style={{ position: "absolute", left: `${random(`gb-x-${i}-${f}`) * -20}%`, top: `${y}%`, width: "140%", height: `${h}%`, background: col, opacity: 0.35 }} />
      );
    })}
  </AbsoluteFill>
);

const LightLeak: React.FC<{ u: number; b: number }> = ({ u, b }) => (
  <AbsoluteFill style={{ mixBlendMode: "screen", opacity: b * 0.85 }}>
    <div style={{ position: "absolute", width: "90%", height: "160%", top: "-30%", left: `${-60 + u * 120}%`, background: "radial-gradient(ellipse, rgba(255,170,90,.95) 0%, rgba(255,90,150,.55) 35%, transparent 70%)", filter: "blur(40px)" }} />
    <div style={{ position: "absolute", width: "60%", height: "120%", top: "-10%", left: `${-20 + u * 90}%`, background: "radial-gradient(ellipse, rgba(255,240,200,.8) 0%, transparent 65%)", filter: "blur(30px)" }} />
  </AbsoluteFill>
);

const Barrido: React.FC<{ u: number; color?: string }> = ({ u, color }) => {
  // los paneles tapan la pantalla justo en el corte (u = 0,5)
  const x = (k: number) => interpolate(u, [k, 0.86 + k], [-130, 130], { ...CL, easing: EASE.seco });
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div style={{ position: "absolute", inset: "-10% -20%", background: C.violet, transform: `translateX(${x(0.08)}%) skewX(-12deg)` }} />
      <div style={{ position: "absolute", inset: "-10% -20%", background: color ?? C.lime, transform: `translateX(${x(0)}%) skewX(-12deg)` }} />
    </AbsoluteFill>
  );
};

// ======================= subtítulos con estilos =======================
export type Palabra = { w: string; s: number; e: number };
const clean = (w: string) => w.toLowerCase().replace(/[.,;:¿?¡!“”"]/g, "");

/** Texto de un bloque de subtítulos según ESTILO.subtitulos. Lo usan Subtitles (lib) y SubsV (reel). */
export const TextoSubs: React.FC<{
  words: Palabra[];
  start: number;
  keywords: string[];
  size: number;
  estilo?: EstiloSubs;
  maxWidth?: number;
}> = ({ words, start, keywords, size, estilo = ESTILO.subtitulos, maxWidth }) => {
  const t = useT();
  const kw = new Set(keywords.map((k) => k.toLowerCase()));
  const p = p01(t, start, 0.25, EASE.rebote);
  const upper = ESTILO.mayusculas || estilo === "pop";
  const base: React.CSSProperties = {
    fontFamily: estilo === "minimal" ? BODY : TITLE,
    fontWeight: estilo === "minimal" ? 600 : 900,
    fontSize: estilo === "minimal" ? size * 0.82 : size,
    lineHeight: 1.08,
    letterSpacing: upper ? 0 : -0.5,
    textTransform: upper ? "uppercase" : "none",
    color: C.text,
    textAlign: "center",
    display: "flex",
    flexWrap: "wrap",
    justifyContent: "center",
    gap: `0 ${Math.round(size * (estilo === "pop" ? 0.4 : 0.28))}px`,
    maxWidth,
  };
  const stroke: React.CSSProperties = {
    WebkitTextStroke: `${Math.max(3, size * 0.07)}px #000`,
    paintOrder: "stroke fill",
    textShadow: "0 5px 0 rgba(0,0,0,.55), 0 10px 30px rgba(0,0,0,.5)",
  };
  const caja = estilo === "caja" || estilo === "karaoke";
  const container: React.CSSProperties = {
    ...base,
    ...(caja ? { padding: "14px 30px", borderRadius: 18, background: "rgba(11,10,16,.66)", backdropFilter: "blur(8px)" } : {}),
    ...(estilo === "contorno" || estilo === "pop" ? stroke : {}),
    ...(estilo === "marcador" || estilo === "minimal" ? { textShadow: "0 3px 18px rgba(0,0,0,.85), 0 1px 3px rgba(0,0,0,.9)" } : {}),
    transform: estilo === "pop" ? "none" : `scale(${0.9 + 0.1 * p})`,
    opacity: estilo === "pop" ? 1 : Math.min(1, p * 2),
  };
  // palabra "actual" para karaoke
  const actual = [...words].reverse().find((w) => t >= w.s);
  return (
    <div style={container}>
      {words.map((w, i) => {
        const spoken = t >= w.s;
        const key = kw.has(clean(w.w));
        const txt = w.w.replace(/[.,]$/, "");
        const st: React.CSSProperties = { display: "inline-block", position: "relative" };
        if (estilo === "pop") {
          if (!spoken) return null; // palabra por palabra: la frase crece centrada
          const q = p01(t, w.s - 0.03, 0.22, EASE.rebote);
          Object.assign(st, {
            opacity: spoken ? 1 : 0,
            transform: `scale(${(key ? 1.14 : 1) * (0.5 + 0.5 * q)}) rotate(${key ? -2 : 0}deg)`,
            color: key ? C.lime : C.text,
            margin: key ? `0 ${Math.round(size * 0.1)}px` : undefined,
          });
        } else if (estilo === "karaoke") {
          const on = actual === w;
          Object.assign(st, {
            color: on ? C.bg : spoken ? (key ? C.lime : C.text) : "rgba(244,242,248,.45)",
            background: on ? (key ? C.lime : C.text) : "transparent",
            borderRadius: 10,
            padding: "0 10px",
            margin: "0 -10px",
          });
        } else if (estilo === "marcador") {
          const m = key ? p01(t, w.s, 0.3) : 0;
          Object.assign(st, {
            color: key && m > 0.5 ? C.bg : spoken ? C.text : "rgba(244,242,248,.55)",
            backgroundImage: key ? `linear-gradient(${C.lime}, ${C.lime})` : undefined,
            backgroundRepeat: "no-repeat",
            backgroundSize: `${m * 100}% 88%`,
            backgroundPosition: "0 60%",
            padding: key ? "0 10px" : undefined,
            borderRadius: 8,
            textShadow: key && m > 0.5 ? "none" : undefined,
          });
        } else if (estilo === "neon") {
          const col = key ? C.lime : C.text;
          Object.assign(st, {
            color: spoken ? col : "rgba(244,242,248,.4)",
            textShadow: spoken ? `0 0 10px ${col}, 0 0 28px ${col}88, 0 0 60px ${col}55` : "none",
          });
        } else if (estilo === "minimal") {
          Object.assign(st, {
            color: spoken ? (key ? C.lime : C.text) : "rgba(244,242,248,.5)",
            borderBottom: key && spoken ? `4px solid ${C.lime}` : "4px solid transparent",
          });
        } else {
          // caja / contorno
          st.color = key && spoken ? C.lime : spoken ? C.text : estilo === "contorno" ? "rgba(244,242,248,.6)" : "rgba(244,242,248,.45)";
        }
        return (
          <span key={i} style={st}>
            {txt}
          </span>
        );
      })}
    </div>
  );
};

// ======================= look de cine (viñeta, grano, barras) =======================
export const Look: React.FC = () => {
  const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const { vineta, grano, barras } = ESTILO.look;
  const bar = barras && width > height ? Math.max(0, (height - width / 2.39) / 2) : 0;
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {vineta > 0 && (
        <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 45%, transparent 52%, rgba(0,0,0,${(0.8 * vineta).toFixed(3)}) 100%)` }} />
      )}
      {grano > 0 && (
        <svg width={width} height={height} style={{ position: "absolute", inset: 0, opacity: grano * 0.4, mixBlendMode: "overlay" }}>
          <filter id="grano">
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={f % 48} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter="url(#grano)" />
        </svg>
      )}
      {bar > 0 && (
        <>
          <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: bar, background: "#000" }} />
          <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: bar, background: "#000" }} />
        </>
      )}
    </AbsoluteFill>
  );
};

// ======================= fondos alternativos =======================
export const FondoPro: React.FC<{ tipo?: TipoFondo }> = ({ tipo = ESTILO.fondo }) => {
  const t = useT();
  if (tipo === "liso") return <AbsoluteFill style={{ background: C.bg }} />;
  if (tipo === "degradado")
    return (
      <AbsoluteFill
        style={{ background: `linear-gradient(${135 + 20 * Math.sin(t * 0.15)}deg, ${C.bg} 0%, ${C.cardSolid} 45%, ${C.violet}55 100%)` }}
      />
    );
  if (tipo === "grilla")
    return (
      <AbsoluteFill style={{ background: C.bg, overflow: "hidden" }}>
        <div
          style={{
            position: "absolute",
            inset: "-50% -50% 0 -50%",
            transform: "perspective(700px) rotateX(62deg)",
            transformOrigin: "50% 100%",
            backgroundImage: `linear-gradient(${C.violet}55 2px, transparent 2px), linear-gradient(90deg, ${C.violet}55 2px, transparent 2px)`,
            backgroundSize: "90px 90px",
            backgroundPosition: `0 ${(t * 45) % 90}px`,
            maskImage: "linear-gradient(to top, black 10%, transparent 75%)",
            WebkitMaskImage: "linear-gradient(to top, black 10%, transparent 75%)",
          }}
        />
        <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 30%, ${C.lime}18 0%, transparent 60%)` }} />
      </AbsoluteFill>
    );
  if (tipo === "particulas")
    return (
      <AbsoluteFill style={{ background: C.bg, overflow: "hidden" }}>
        {Array.from({ length: 46 }).map((_, i) => {
          const x = random(`px-${i}`) * 100;
          const sp = 8 + random(`ps-${i}`) * 22;
          const y = (random(`py-${i}`) * 120 - t * sp * 0.4) % 120;
          const s = 3 + random(`pz-${i}`) * 9;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: `${x}%`,
                top: `${y < -10 ? y + 120 : y}%`,
                width: s,
                height: s,
                borderRadius: 99,
                background: i % 3 ? C.violet : C.lime,
                opacity: 0.15 + random(`po-${i}`) * 0.35,
                filter: `blur(${s > 8 ? 2 : 0}px)`,
              }}
            />
          );
        })}
      </AbsoluteFill>
    );
  // ondas
  return (
    <AbsoluteFill style={{ background: C.bg, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          backgroundImage: `repeating-radial-gradient(circle at 70% 40%, transparent 0, transparent ${60 + ((t * 20) % 60)}px, ${C.violet}22 ${62 + ((t * 20) % 60)}px, transparent ${66 + ((t * 20) % 60)}px)`,
        }}
      />
      <AbsoluteFill style={{ background: `radial-gradient(circle at 70% 40%, ${C.violet}30 0%, transparent 55%)` }} />
    </AbsoluteFill>
  );
};

// ======================= texto cinético =======================
/**
 * Frase grande animada palabra por palabra (alternativa a Quote para no repetir siempre lo mismo).
 * estilo: "impacto" (golpe con desenfoque) · "ola" (suben en ola) · "maquina" (letra por letra) · "apilado" (póster)
 */
export const TextoCinetico: React.FC<{
  from: number;
  to: number;
  lines: [string, number][][];
  mark?: string;
  estilo?: "impacto" | "ola" | "maquina" | "apilado";
  size?: number;
  fondo?: boolean;
  style?: React.CSSProperties;
}> = ({ from, to, lines, mark, estilo = "impacto", size = 96, fondo = true, style }) => {
  const t = useT();
  if (t < from - 0.1 || t > to + 0.4) return null;
  const o = p01(t, from, 0.3) * (1 - p01(t, to, 0.3));
  return (
    <AbsoluteFill style={{ opacity: o }}>
      {fondo && <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 55%, rgba(11,10,16,.75) 0%, rgba(11,10,16,.35) 70%)" }} />}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", gap: 6, ...style }}>
        {lines.map((line, li) => {
          const big = estilo === "apilado" ? (li % 2 === 0 ? 1.25 : 0.7) : 1;
          return (
            <div key={li} style={{ display: "flex", gap: size * big * 0.32, flexWrap: "wrap", justifyContent: "center", maxWidth: "90%" }}>
              {line.map(([w, at], wi) => {
                const isMark = !!mark && w.replace(/[“”".,!?¡¿]/g, "").toLowerCase() === mark.toLowerCase();
                let st: React.CSSProperties = {};
                let text: React.ReactNode = w;
                if (estilo === "impacto") {
                  const q = p01(t, at, 0.28, EASE.seco);
                  st = { opacity: q, transform: `scale(${1.9 - 0.9 * q})`, filter: `blur(${(1 - q) * 14}px)` };
                } else if (estilo === "ola") {
                  const q = p01(t, at, 0.45, EASE.rebote);
                  st = { opacity: Math.min(1, q * 1.5), transform: `translateY(${(1 - q) * 70}px) rotate(${(1 - q) * 8}deg)` };
                } else if (estilo === "maquina") {
                  const n = Math.max(0, Math.min(w.length, Math.floor((t - at) / 0.035)));
                  text = w.slice(0, n);
                  st = { opacity: t >= at ? 1 : 0 };
                } else {
                  const q = p01(t, at, 0.4);
                  const side = (li + wi) % 2 ? 1 : -1;
                  st = { opacity: q, transform: `translateX(${(1 - q) * side * 120}px)` };
                }
                const m = isMark ? p01(t, at + 0.15, 0.35) : 0;
                return (
                  <span
                    key={wi}
                    style={{
                      display: "inline-block",
                      position: "relative",
                      isolation: "isolate",
                      fontFamily: TITLE,
                      fontWeight: 900,
                      fontSize: size * big,
                      letterSpacing: -2,
                      lineHeight: 1.02,
                      textTransform: estilo === "apilado" ? "uppercase" : "none",
                      color: isMark && m > 0.4 ? C.bg : C.text,
                      textShadow: isMark && m > 0.4 ? "none" : "0 6px 30px rgba(0,0,0,.6)",
                      margin: isMark ? `0 ${Math.round(size * big * 0.12)}px` : undefined,
                      ...st,
                    }}
                  >
                    {isMark && (
                      <span style={{ position: "absolute", left: -12, right: -12, top: "12%", bottom: "6%", background: C.lime, borderRadius: 12, zIndex: -1, transform: `scaleX(${m})`, transformOrigin: "0 50%" }} />
                    )}
                    {text}
                  </span>
                );
              })}
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// ======================= llamadas de atención =======================
/** Círculo dibujado a mano alrededor de algo (x, y = centro en px del video). */
export const Circulo: React.FC<{ at: number; to: number; x: number; y: number; w: number; h: number; color?: string; grosor?: number }> = ({
  at, to, x, y, w, h, color = C.lime, grosor = 9,
}) => {
  const t = useT();
  if (t < at || t > to + 0.3) return null;
  const p = p01(t, at, 0.55, EASE.lento);
  const o = 1 - p01(t, to, 0.3);
  const rx = w / 2, ry = h / 2;
  // elipse con un poco de "sobretrazo" para que parezca hecha a mano
  const d = `M ${rx * 2 - 4} ${ry} A ${rx} ${ry} 0 1 0 ${rx * 2 - 10} ${ry * 0.72}`;
  return (
    <svg style={{ position: "absolute", left: x - rx - grosor, top: y - ry - grosor, overflow: "visible", opacity: o, transform: "rotate(-4deg)" }} width={w + grosor * 2} height={h + grosor * 2}>
      <path d={d} transform={`translate(${grosor},${grosor})`} fill="none" stroke={color} strokeWidth={grosor} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} style={{ filter: `drop-shadow(0 0 12px ${color}88)` }} />
    </svg>
  );
};

/** Flecha curva que se dibuja apuntando a (x, y). `angulo` = desde dónde viene (grados, 0 = desde la izquierda). */
export const Flecha: React.FC<{ at: number; to: number; x: number; y: number; angulo?: number; largo?: number; color?: string }> = ({
  at, to, x, y, angulo = 0, largo = 240, color = C.lime,
}) => {
  const t = useT();
  if (t < at || t > to + 0.3) return null;
  const p = p01(t, at, 0.45, EASE.lento);
  const head = p01(t, at + 0.35, 0.2, EASE.rebote);
  const o = 1 - p01(t, to, 0.3);
  const L = largo;
  return (
    <div style={{ position: "absolute", left: x, top: y, width: 0, height: 0, transform: `rotate(${angulo}deg)`, opacity: o }}>
      <svg style={{ position: "absolute", left: -L - 20, top: -L * 0.4, overflow: "visible" }} width={L + 40} height={L * 0.8}>
        <path d={`M 0 ${L * 0.55} C ${L * 0.35} ${L * 0.05}, ${L * 0.7} ${L * 0.05}, ${L} ${L * 0.4}`} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
        <g transform={`translate(${L} ${L * 0.4}) rotate(48) scale(${head})`}>
          <path d="M -34 -14 L 0 0 L -30 22" fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" strokeLinejoin="round" />
        </g>
      </svg>
    </div>
  );
};

/** Emoji que salta a pantalla, flota y se va. */
export const EmojiPop: React.FC<{ at: number; to: number; emoji: string; x: number; y: number; size?: number }> = ({ at, to, emoji, x, y, size = 130 }) => {
  const t = useT();
  if (t < at || t > to + 0.35) return null;
  const q = p01(t, at, 0.6, EASE.elastico);
  const out = p01(t, to, 0.3);
  return (
    <div
      style={{
        position: "absolute",
        left: x - size / 2,
        top: y - size / 2 + Math.sin((t - at) * 3) * 8,
        fontSize: size,
        lineHeight: 1,
        transform: `scale(${q * (1 - out * 0.4)}) rotate(${Math.sin((t - at) * 2.2) * 6}deg)`,
        opacity: 1 - out,
        filter: "drop-shadow(0 10px 25px rgba(0,0,0,.45))",
      }}
    >
      {emoji}
    </div>
  );
};

/** Barra fina de progreso del video (arriba). Ayuda a la retención en videos largos. */
export const BarraProgreso: React.FC<{ color?: string; alto?: number; abajo?: boolean }> = ({ color = C.lime, alto = 7, abajo = false }) => {
  const f = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div style={{ position: "absolute", left: 0, right: 0, [abajo ? "bottom" : "top"]: 0, height: alto, background: "rgba(255,255,255,.08)" }}>
      <div style={{ width: `${(f / durationInFrames) * 100}%`, height: "100%", background: color, boxShadow: `0 0 12px ${color}` }} />
    </div>
  );
};

// ======================= ritmo de la música =======================
/** Lleva un tiempo al golpe de la música más cercano (si hay uno a menos de `max` s). Requiere scripts/ritmo.py. */
export const alBeat = (t: number, max = 0.25) => {
  let best = t;
  let d = max;
  for (const b of BEATS) {
    const x = Math.abs(b - t);
    if (x < d) { d = x; best = b; }
  }
  return best;
};

// ======================= efectos de sonido con variantes =======================
export type SfxName =
  | "whoosh" | "pop" | "ding" | "click" | "boom" | "riser" | "swoosh" | "glitch" | "impacto" | "shutter" | "tecleo" | "brillo";
/** Archivos de public/sfx/ por tipo. Se rotan en orden y con leve variación de tono/volumen para que no suenen repetidos. */
export const SFX_VARIANTES: Record<SfxName, string[]> = {
  whoosh: ["whoosh", "whoosh_2", "whoosh_3"],
  pop: ["pop", "pop_2", "pop_3"],
  ding: ["ding", "ding_2"],
  click: ["click", "click_2"],
  boom: ["boom", "boom_2"],
  riser: ["riser"],
  swoosh: ["swoosh", "swoosh_2"],
  glitch: ["glitch"],
  impacto: ["impacto"],
  shutter: ["shutter"],
  tecleo: ["tecleo"],
  brillo: ["brillo"],
};

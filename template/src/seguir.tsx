// Objetos que SIGUEN a la persona (manos, dedos, cara, hombros) y objetos que se MUEVEN por un recorrido.
// Los datos de seguimiento los genera scripts/seguir.py → src/puntos.ts. Catálogo: references/seguimiento.md
// NO editar por video: se usa desde video.tsx.
import React from "react";
import { AbsoluteFill, Easing, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PUNTOS, GESTOS, PASO, Punto, Gesto } from "./puntos";
import { EASE, p01 } from "./fx";

const useT = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return f / fps;
};
const CL = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export type NombrePunto = keyof typeof PUNTOS | string;

/** Muestra una pista en el segundo t (interpolada). Devuelve null si en ese momento no se ve. */
export const muestra = (nombre: NombrePunto, t: number): Punto => {
  const tr = (PUNTOS as Record<string, Punto[]>)[nombre];
  if (!tr || !tr.length) return null;
  const k = t / PASO;
  const i = Math.floor(k);
  if (i < 0 || i >= tr.length) return null;
  const a = tr[i];
  const b = tr[Math.min(i + 1, tr.length - 1)];
  if (!a) return b && k - i > 0.5 ? b : null;
  if (!b) return a;
  const u = k - i;
  return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];
};

/**
 * Posición con inercia: media ponderada de las últimas muestras (el objeto llega "un poco después"
 * que la mano, como si tuviera peso). inercia 0 = pegado · 0.25 = natural · 0.6 = muy flotante.
 * Es determinista (no guarda estado), así que el render sale igual siempre.
 */
export const posicion = (nombre: NombrePunto, t: number, inercia = 0.25): Punto => {
  if (inercia <= 0.01) return muestra(nombre, t);
  const lag = inercia * 0.6; // segundos de "arrastre"
  const n = 6;
  let sx = 0, sy = 0, sw = 0, vistos = 0;
  for (let i = 0; i < n; i++) {
    const dt = (lag * i) / (n - 1);
    const p = muestra(nombre, t - dt);
    const w = Math.exp(-2.2 * (i / (n - 1)));
    if (p) { sx += p[0] * w; sy += p[1] * w; sw += w; vistos++; }
  }
  if (!sw || vistos < 2) return muestra(nombre, t);
  return [sx / sw, sy / sw];
};

/** ¿Cuánto se está moviendo ese punto? (0 = quieto, 1 = rápido). Para estelas o escalas por velocidad. */
export const velocidad = (nombre: NombrePunto, t: number): number => {
  const a = muestra(nombre, t - PASO);
  const b = muestra(nombre, t + PASO);
  if (!a || !b) return 0;
  return Math.min(1, Math.hypot(b[0] - a[0], b[1] - a[1]) / (PASO * 2) / 60);
};

/** Tiempo del gesto nº `n` (0 = el primero). `mano` opcional. Devuelve null si no hay tantos. */
export const gestoEn = (gesto: Gesto, n = 0, mano?: "izq" | "der"): number | null => {
  const l = GESTOS.filter((g) => g.gesto === gesto && (!mano || g.mano === mano));
  return l[n] ? l[n].t : null;
};

type Aparicion = "pop" | "fade" | "destello" | "ninguna";
const entrada = (ap: Aparicion, t: number, from: number, to: number) => {
  const out = p01(t, to, 0.3);
  if (ap === "ninguna") return { o: 1 - out, s: 1 };
  if (ap === "fade") return { o: p01(t, from, 0.35) * (1 - out), s: 1 };
  if (ap === "destello") {
    const i = p01(t, from, 0.45, EASE.rebote);
    return { o: p01(t, from, 0.2) * (1 - out), s: 0.4 + 0.6 * i, glow: 1 - p01(t, from, 0.6) };
  }
  const i = p01(t, from, 0.5, EASE.elastico);
  return { o: p01(t, from, 0.18) * (1 - out), s: 0.3 + 0.7 * i };
};

/**
 * Pega cualquier contenido a un punto del cuerpo: `<Seguir punto="manoDer" from={3} to={8}>…</Seguir>`
 * - `offset`: desplazamiento en px (coordenadas del video) respecto al punto.
 * - `inercia`: 0 pegado · 0.25 natural · 0.6 flotante.
 * - `flotar`: amplitud en px de un vaivén suave (0 = sin flote).
 * - `giroPorVelocidad`: inclina el objeto hacia donde se mueve la mano.
 * - `ocultarSinPunto`: si la mano desaparece, el objeto se desvanece (true) o se queda quieto (false).
 */
export const Seguir: React.FC<{
  punto: NombrePunto;
  from: number;
  to: number;
  children: React.ReactNode;
  offset?: [number, number];
  inercia?: number;
  flotar?: number;
  escala?: number;
  giroPorVelocidad?: boolean;
  aparece?: Aparicion;
  ocultarSinPunto?: boolean;
}> = ({ punto, from, to, children, offset = [0, 0], inercia = 0.25, flotar = 8, escala = 1,
       giroPorVelocidad = false, aparece = "pop", ocultarSinPunto = true }) => {
  const t = useT();
  const { width, height } = useVideoConfig();
  if (t < from - 0.1 || t > to + 0.4) return null;
  const p = posicion(punto, t, inercia);
  if (!p && ocultarSinPunto) return null;
  const pos = p ?? [50, 50];
  const { o, s, glow } = entrada(aparece, t, from, to);
  // se desvanece cuando el punto deja de verse
  const visible = muestra(punto, t) ? 1 : 0.35;
  const fy = flotar ? Math.sin((t - from) * 2.1) * flotar : 0;
  const fx = flotar ? Math.cos((t - from) * 1.4) * flotar * 0.5 : 0;
  const giro = giroPorVelocidad ? (() => {
    const a = muestra(punto, t - PASO), b = muestra(punto, t + PASO);
    return a && b ? Math.max(-22, Math.min(22, (b[0] - a[0]) * 2.2)) : 0;
  })() : 0;
  return (
    <div
      style={{
        position: "absolute",
        left: (pos[0] / 100) * width + offset[0] + fx,
        top: (pos[1] / 100) * height + offset[1] + fy,
        transform: `translate(-50%, -50%) scale(${s * escala}) rotate(${giro}deg)`,
        opacity: o * visible,
        filter: glow ? `drop-shadow(0 0 ${glow * 40}px rgba(255,255,255,.9))` : undefined,
        pointerEvents: "none",
      }}
    >
      {children}
    </div>
  );
};

// ======================= recorridos libres =======================
export type Curva = "suave" | "lineal" | "rebote" | "elastico" | "seco";
const CURVAS: Record<Curva, (x: number) => number> = {
  suave: EASE.suave as any,
  lineal: (x) => x,
  rebote: EASE.rebote as any,
  elastico: EASE.elastico as any,
  seco: EASE.seco as any,
};

/** Un punto del recorrido. x/y en % del cuadro (0–100); o `punto` para aterrizar en una mano/cara. */
export type Paso = {
  at: number;
  x?: number;
  y?: number;
  punto?: NombrePunto;
  escala?: number;
  giro?: number;
  opacidad?: number;
  curva?: Curva;
};

const valorPaso = (p: Paso, t: number): [number, number] => {
  if (p.punto) {
    const q = muestra(p.punto, t);
    if (q) return q;
  }
  return [p.x ?? 50, p.y ?? 50];
};

/**
 * Mueve un objeto por un recorrido de puntos clave. Entre dos pasos usa la curva del paso de destino.
 * `curvo` redondea las esquinas (trayectoria tipo arco, se ve mucho más natural que una línea recta).
 * Un paso puede apuntar a `punto: "manoDer"`: el objeto sale de la mano o aterriza en ella.
 */
export const Mover: React.FC<{
  pasos: Paso[];
  children: React.ReactNode;
  curvo?: boolean;
  estela?: number;
}> = ({ pasos, children, curvo = true, estela = 0 }) => {
  const t = useT();
  const { width, height } = useVideoConfig();
  const ks = [...pasos].sort((a, b) => a.at - b.at);
  if (!ks.length || t < ks[0].at - 0.05 || t > ks[ks.length - 1].at + 0.4) return null;
  let i = 0;
  while (i + 1 < ks.length && ks[i + 1].at <= t) i++;
  const cur = ks[i];
  const nxt = ks[Math.min(i + 1, ks.length - 1)];
  const dur = Math.max(0.001, nxt.at - cur.at);
  const u = nxt === cur ? 1 : Math.min(1, Math.max(0, (t - cur.at) / dur));
  const e = CURVAS[nxt.curva ?? "suave"];
  const k = typeof e === "function" ? (e as any)(u) : u;
  const a = valorPaso(cur, t);
  const b = valorPaso(nxt, t);
  let x = a[0] + (b[0] - a[0]) * k;
  let y = a[1] + (b[1] - a[1]) * k;
  if (curvo && nxt !== cur) {
    // arco: se separa de la recta en el medio, perpendicular al trayecto
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const arco = Math.sin(Math.PI * k) * 0.16;
    x += -dy * arco;
    y += dx * arco * 0.5;
  }
  const mix = (p: Paso, q: Paso, key: "escala" | "giro" | "opacidad", def: number) =>
    (p[key] ?? def) + ((q[key] ?? def) - (p[key] ?? def)) * k;
  const sc = mix(cur, nxt, "escala", 1);
  const gi = mix(cur, nxt, "giro", 0);
  const op = mix(cur, nxt, "opacidad", 1) * (1 - p01(t, ks[ks.length - 1].at, 0.3));
  const estelas = estela
    ? Array.from({ length: estela }).map((_, n) => ({ d: (n + 1) * 0.055, o: 0.3 * (1 - n / estela) }))
    : [];
  return (
    <>
      {estelas.map((s, n) => (
        <MoverSombra key={n} pasos={ks} curvo={curvo} dt={s.d} opacidad={s.o * op}>
          {children}
        </MoverSombra>
      ))}
      <div
        style={{
          position: "absolute",
          left: (x / 100) * width,
          top: (y / 100) * height,
          transform: `translate(-50%, -50%) scale(${sc}) rotate(${gi}deg)`,
          opacity: op,
          pointerEvents: "none",
        }}
      >
        {children}
      </div>
    </>
  );
};

const MoverSombra: React.FC<{ pasos: Paso[]; curvo: boolean; dt: number; opacidad: number; children: React.ReactNode }> = ({
  pasos, curvo, dt, opacidad, children,
}) => {
  const t = useT() - dt;
  const { width, height } = useVideoConfig();
  if (t < pasos[0].at) return null;
  let i = 0;
  while (i + 1 < pasos.length && pasos[i + 1].at <= t) i++;
  const cur = pasos[i], nxt = pasos[Math.min(i + 1, pasos.length - 1)];
  const u = nxt === cur ? 1 : Math.min(1, Math.max(0, (t - cur.at) / Math.max(0.001, nxt.at - cur.at)));
  const e = CURVAS[nxt.curva ?? "suave"];
  const k = typeof e === "function" ? (e as any)(u) : u;
  const a = valorPaso(cur, t), b = valorPaso(nxt, t);
  let x = a[0] + (b[0] - a[0]) * k, y = a[1] + (b[1] - a[1]) * k;
  if (curvo && nxt !== cur) {
    const dx = b[0] - a[0], dy = b[1] - a[1], arco = Math.sin(Math.PI * k) * 0.16;
    x += -dy * arco; y += dx * arco * 0.5;
  }
  return (
    <div style={{ position: "absolute", left: (x / 100) * width, top: (y / 100) * height,
                  transform: "translate(-50%, -50%)", opacity: opacidad, filter: "blur(2px)", pointerEvents: "none" }}>
      {children}
    </div>
  );
};

// ---------- movimientos listos ----------
/** Órbita alrededor de un punto (p. ej. tu cabeza). `radio` en px, `vueltas` por el tramo. */
export const Orbita: React.FC<{
  punto?: NombrePunto; cx?: number; cy?: number; from: number; to: number;
  radio?: number; vueltas?: number; fase?: number; aplanar?: number; children: React.ReactNode;
}> = ({ punto, cx = 50, cy = 50, from, to, radio = 260, vueltas = 1, fase = 0, aplanar = 0.45, children }) => {
  const t = useT();
  const { width, height } = useVideoConfig();
  if (t < from - 0.1 || t > to + 0.4) return null;
  const u = (t - from) / Math.max(0.001, to - from);
  const ang = fase * Math.PI * 2 + u * vueltas * Math.PI * 2;
  const base = punto ? muestra(punto, t) : null;
  const bx = base ? (base[0] / 100) * width : (cx / 100) * width;
  const by = base ? (base[1] / 100) * height : (cy / 100) * height;
  const detras = Math.cos(ang) < 0;
  const o = p01(t, from, 0.4) * (1 - p01(t, to, 0.3));
  return (
    <div
      style={{
        position: "absolute",
        left: bx + Math.sin(ang) * radio,
        top: by + Math.cos(ang) * radio * aplanar,
        transform: `translate(-50%, -50%) scale(${0.78 + 0.22 * (detras ? 0 : 1) + 0.12 * Math.cos(ang)})`,
        opacity: o * (detras ? 0.55 : 1),
        pointerEvents: "none",
      }}
    >
      {children}
    </div>
  );
};

// ======================= profundidad (el objeto pasa DETRÁS de la persona) =======================
/**
 * Capa con la persona recortada (public/persona.webm, lo genera `fondo.py --modo matte`).
 * Poner DESPUÉS del objeto que debe quedar detrás:  <Camera/> … <objeto/> <Persona/>
 */
export const Persona: React.FC<{ archivo?: string }> = ({ archivo = "persona.webm" }) => (
  <AbsoluteFill>
    <OffthreadVideo src={staticFile(archivo)} transparent muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
  </AbsoluteFill>
);

// ======================= piezas visuales para seguir/mover =======================
/** Burbuja redonda con un emoji o un logo dentro (lo más usado sobre la mano). */
export const Burbuja: React.FC<{ children: React.ReactNode; size?: number; color?: string; brillo?: boolean }> = ({
  children, size = 150, color = "rgba(21,19,28,.88)", brillo = true,
}) => (
  <div
    style={{
      width: size, height: size, borderRadius: 9999, background: color,
      border: "2px solid rgba(255,255,255,.14)", backdropFilter: "blur(10px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: size * 0.5, lineHeight: 1,
      boxShadow: brillo ? "0 18px 50px rgba(0,0,0,.5), 0 0 40px rgba(167,123,255,.35)" : "0 18px 50px rgba(0,0,0,.5)",
    }}
  >
    {children}
  </div>
);

/** Chispas que salen de un punto (para "chasquido" o cuando algo aparece en la mano). */
export const Chispas: React.FC<{ at: number; dur?: number; n?: number; color?: string; radio?: number }> = ({
  at, dur = 0.9, n = 14, color = "#D7F25A", radio = 220,
}) => {
  const t = useT();
  if (t < at || t > at + dur) return null;
  const u = (t - at) / dur;
  return (
    <>
      {Array.from({ length: n }).map((_, i) => {
        const ang = (i / n) * Math.PI * 2 + i * 0.7;
        const d = radio * Math.pow(u, 0.55) * (0.6 + ((i * 37) % 10) / 14);
        const s = 12 * (1 - u) * (0.6 + ((i * 17) % 7) / 7);
        return (
          <div key={i} style={{ position: "absolute", left: Math.sin(ang) * d, top: Math.cos(ang) * d,
                                width: s, height: s, borderRadius: 9999, background: color,
                                opacity: 1 - u, transform: "translate(-50%,-50%)",
                                boxShadow: `0 0 ${s * 2}px ${color}` }} />
        );
      })}
    </>
  );
};

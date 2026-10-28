// Reel "Método 3" — estilo Creador pro con íconos 3D, animaciones explicativas en pantalla dividida
// y ESCENAS DE FLUJO a pantalla completa (la persona sale del plano y el concepto se explica solo
// con etapas, flechas e íconos). Ver `references/preset-creador-pro.md`.
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { DURATION, WORDS } from "./words";
import { Sfx, Sounds, useT, pop, prog } from "./lib";
import { ConTransiciones, Look, Transicion, sfxDeTransiciones } from "./fx";
import { CamKeyV, CAM_BOTTOM, CAM_FULL, DualCam } from "./reel";

const { fontFamily: ANTON } = loadAnton("normal", { weights: ["400"], subsets: ["latin"] });
const { fontFamily: INTER } = loadInter("normal", { weights: ["600", "800"], subsets: ["latin"] });

export const CTA_SECONDS = 1.0;

const GOLD = "linear-gradient(180deg,#FFF0A6 0%,#FFD23C 38%,#F2A900 72%,#B97800 100%)";
const NARANJA = "#FF9F1C";
const AZUL = "#3B7BFF";
const ic = (n: string) => staticFile(`iconos/${n}_3d.png`);

// ---------- cámara ----------
const full = (at: number, zoom = 1): CamKeyV => ({ at, box: CAM_FULL, zoom });
const split = (at: number): CamKeyV => ({ at, box: CAM_BOTTOM });
const CAM: CamKeyV[] = [
  full(0), full(0.88, 1.14),
  split(3.2),                        // panel: los 3 métodos
  full(9.0), full(9.36, 1.16),
  full(10.9),                        // (tapado por la escena de flujo)
  full(17.5, 1.2), full(19.9, 1.0), full(22.2, 1.14), full(24.7, 1.22), full(26.8, 1.0),
  full(28.5),                        // (tapado por la escena de flujo)
  full(34.4, 1.0), full(35.9, 1.22), full(38.1, 1.0), full(41.6, 1.14), full(44.6, 1.0), full(47.5, 1.2), full(49.5, 1.0),
  split(50.0),                       // panel: el spinner
  full(54.0),
];
const esSplit = (t: number) => {
  let i = 0;
  while (i + 1 < CAM.length && CAM[i + 1].at <= t) i++;
  return CAM[i].box.h < 1500;
};

// ESCENAS a pantalla completa (la cara sale del plano a propósito: cambio de enfoque).
// Declararlas también en caracheck.py --escenas.
const ESCENA_FLUJO_A: [number, number] = [10.95, 17.45];
const ESCENA_FLUJO_B: [number, number] = [28.55, 34.35];
const FINAL = 54.2;
const ESCENAS: [number, number][] = [ESCENA_FLUJO_A, ESCENA_FLUJO_B, [FINAL, 999]];
const enEscena = (t: number) => ESCENAS.some(([a, b]) => t >= a - 0.05 && t <= b);

const TRANS: Transicion[] = [
  { at: 3.2, tipo: "latigo" }, { at: 9.0, tipo: "flash" }, { at: 10.95, tipo: "zoom" }, { at: 17.45, tipo: "desenfoque" },
  { at: 24.7, tipo: "flash" }, { at: 28.55, tipo: "latigo" }, { at: 34.35, tipo: "zoom" }, { at: 41.6, tipo: "sacudida" },
  { at: 47.5, tipo: "desenfoque" }, { at: 50.0, tipo: "flash" }, { at: 54.2, tipo: "zoom" },
];

const BN: [number, number][] = [[17.5, 19.8], [38.1, 41.4]];

type Big = { from: number; to: number; lines: string[]; icono: string };
const BIGS: Big[] = [
  { from: 0.88, to: 2.9, lines: ["FACTORES", "EXTRAORDINARIOS"], icono: "high_voltage" },
  { from: 9.36, to: 10.7, lines: ["UNA PANDEMIA"], icono: "microbe" },
  { from: 20.68, to: 22.1, lines: ["BUSCAR DE VERDAD"], icono: "magnifying_glass_tilted_left" },
  { from: 24.7, to: 26.6, lines: ["EL MUNDIAL"], icono: "soccer_ball" },
  { from: 35.9, to: 37.7, lines: ["CIERTA", "INTUICIÓN"], icono: "brain" },
  { from: 47.5, to: 49.4, lines: ["MÁS DIFÍCIL", "DE EXPLICAR"], icono: "red_question_mark" },
];

// ---------- piezas base ----------
const Gold: React.FC<{ children: React.ReactNode; size: number; stroke?: number; style?: React.CSSProperties }> = ({
  children, size, stroke = 11, style,
}) => (
  <div style={{ position: "relative", display: "inline-block", fontFamily: ANTON, fontSize: size, lineHeight: 0.98, transform: "skewX(-8deg)", letterSpacing: 1, ...style }}>
    <span style={{ position: "absolute", inset: 0, color: "#0b0b0d", WebkitTextStroke: `${stroke}px #0b0b0d`, filter: "drop-shadow(0 10px 18px rgba(0,0,0,.55))" }}>{children}</span>
    <span style={{ position: "relative", background: GOLD, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>{children}</span>
  </div>
);

const Icono3D: React.FC<{ n: string; at: number; size?: number; style?: React.CSSProperties }> = ({ n, at, size = 200, style }) => {
  const t = useT();
  const p = pop(t, at, 0.5);
  return (
    <Img
      src={ic(n)}
      style={{
        width: size, height: size, flexShrink: 0,
        transform: `translateY(${Math.sin((t - at) * 4.6) * 6}px) scale(${p}) rotate(${(1 - p) * -22 + Math.sin((t - at) * 2.8) * 3}deg)`,
        filter: "drop-shadow(0 14px 22px rgba(0,0,0,.5))",
        ...style,
      }}
    />
  );
};

const Hook: React.FC = () => {
  const t = useT();
  if (t > 3.3) return null;
  return (
    <div style={{ position: "absolute", left: 54, top: 232, display: "flex", flexDirection: "column", gap: 2 }}>
      {["EL MÉTODO", "QUE CASI", "NADIE USA"].map((l, i) => {
        const p = pop(t, 0.1 + i * 0.15, 0.45);
        const out = prog(t, 2.9, 0.3);
        return (
          <div key={l} style={{ transform: `translateX(${(1 - p) * -90 - out * 160}px) scale(${0.86 + 0.14 * p})`, opacity: p * (1 - out), transformOrigin: "left center" }}>
            <Gold size={136}>{l}</Gold>
          </div>
        );
      })}
    </div>
  );
};

const BigPhrase: React.FC = () => {
  const t = useT();
  const b = BIGS.find((x) => t >= x.from - 0.05 && t <= x.to + 0.2);
  if (!b) return null;
  const p = pop(t, b.from, 0.4);
  const out = 1 - prog(t, b.to, 0.2);
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 1052, display: "flex", alignItems: "center", justifyContent: "center", gap: 24, opacity: out }}>
      <Icono3D n={b.icono} at={b.from} size={186} />
      <div style={{ transform: `scale(${0.72 + 0.28 * p})`, opacity: p, transformOrigin: "left center", display: "flex", flexDirection: "column", gap: 2 }}>
        {b.lines.map((l) => <Gold key={l} size={b.lines.length > 1 ? 100 : 118} stroke={9}>{l}</Gold>)}
      </div>
    </div>
  );
};

// ---------- subtítulos ----------
type Chunk = { s: number; e: number; text: string };
const CHUNKS: Chunk[] = (() => {
  const out: Chunk[] = [];
  let cur: typeof WORDS = [];
  const flush = () => {
    if (cur.length) { out.push({ s: cur[0].s, e: cur[cur.length - 1].e, text: cur.map((w) => w.w).join(" ") }); cur = []; }
  };
  WORDS.forEach((w, i) => {
    cur.push(w);
    const gap = (WORDS[i + 1]?.s ?? 999) - w.e;
    if (cur.length >= 3 || /[.,?!:;]$/.test(w.w) || gap > 0.45) flush();
  });
  flush();
  return out.map((c, i) => ({ ...c, e: Math.min(c.e + 0.18, out[i + 1]?.s ?? c.e + 0.4) }));
})();

const Subs: React.FC = () => {
  const t = useT();
  if (enEscena(t)) return null;                       // las escenas traen su propio texto
  if (BIGS.some((b) => t >= b.from - 0.02 && t <= b.to + 0.15)) return null;
  const c = CHUNKS.find((x) => t >= x.s && t < x.e);
  if (!c) return null;
  const p = pop(t, c.s, 0.18);
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: esSplit(t) ? 1448 : 1176, textAlign: "center", pointerEvents: "none" }}>
      <span style={{ fontFamily: INTER, fontWeight: 800, fontSize: esSplit(t) ? 62 : 70, letterSpacing: -2.5, color: "#fff", display: "inline-block", transform: `scale(${0.9 + 0.1 * p})`, textShadow: "0 3px 6px rgba(0,0,0,.6), 0 0 24px rgba(0,0,0,.5)" }}>
        {c.text}
      </span>
    </div>
  );
};

// ---------- panel de pantalla dividida ----------
const Panel: React.FC<{ from: number; to: number; children: React.ReactNode; alto?: number }> = ({ from, to, children, alto = 560 }) => {
  const t = useT();
  if (t < from - 0.05 || t > to + 0.45) return null;
  const p = pop(t, from, 0.5);
  const out = prog(t, to, 0.32);
  return (
    <div
      style={{
        position: "absolute", left: 44, top: 252, width: 992, height: alto, padding: "30px 36px",
        background: "linear-gradient(170deg,#ffffff 0%,#eef2fb 100%)", borderRadius: 40,
        boxShadow: "0 44px 90px rgba(0,0,0,.5)", fontFamily: INTER, color: "#10142a",
        transform: `translateY(${(1 - p) * -70}px) scale(${(0.88 + 0.12 * p) * (1 - out * 0.08)}) rotate(${(1 - p) * -2}deg)`,
        opacity: p * (1 - out), transformOrigin: "50% 0%", overflow: "hidden",
      }}
    >
      {children}
    </div>
  );
};

const Rotulo: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <div style={{ fontWeight: 800, fontSize: 30, letterSpacing: 3, color: "#7d85a0" }}>{children}</div>
);

const Traza: React.FC<{ d: string; p: number; color?: string; w?: number }> = ({ d, p, color = AZUL, w = 9 }) => (
  <path d={d} fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />
);

const D_ESTACIONAL = "M12,96 C38,96 42,30 68,30 C94,30 98,96 124,96 C150,96 154,26 180,26 C206,26 210,96 236,96";
const D_COTIDIANO = "M12,66 L52,61 L92,69 L132,62 L172,68 L212,62 L236,66";
const D_PICO = "M12,96 L70,93 L110,95 L146,91 L172,16 L198,44 L236,34";

const TresMetodos: React.FC<{ from: number }> = ({ from }) => {
  const t = useT();
  const items = [
    { n: "01", tit: "Según la época", sub: "Navidad, Halloween", d: D_ESTACIONAL, at: from + 0.5 },
    { n: "02", tit: "Uso cotidiano", sub: "todo el año", d: D_COTIDIANO, at: from + 2.5 },
    { n: "03", tit: "Factores externos", sub: "de la nada", d: D_PICO, at: from + 4.3 },
  ];
  return (
    <>
      <Rotulo>LOS 3 MÉTODOS</Rotulo>
      <div style={{ display: "flex", gap: 16, marginTop: 18 }}>
        {items.map((m, i) => {
          const p = pop(t, m.at, 0.5);
          const vivo = prog(t, m.at, 0.35);
          const activo = i === 2 && t >= m.at + 0.45;
          const trazo = prog(t, m.at + 0.15, 0.85);
          return (
            <div
              key={m.n}
              style={{
                flex: 1, borderRadius: 28, padding: "18px 16px 10px",
                background: activo ? "#10142a" : "#ffffff",
                border: `3px solid ${activo ? "#FFD23C" : "#dde3f2"}`,
                boxShadow: activo ? "0 18px 40px rgba(255,180,0,.45)" : "0 10px 22px rgba(20,30,70,.10)",
                opacity: (0.3 + 0.7 * vivo) * (t >= items[2].at + 0.45 && i < 2 ? 0.5 : 1),
                transform: `translateY(${(1 - p) * 18}px) scale(${activo ? 1.04 : 1})`,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ fontFamily: ANTON, fontSize: 40, color: activo ? "#FFD23C" : "#aab3c9" }}>{m.n}</div>
                <Img src={ic(activo ? "check_mark_button" : "cross_mark")} style={{ width: 40, height: 40, opacity: prog(t, m.at + 0.5, 0.3) }} />
              </div>
              <svg viewBox="0 0 248 110" style={{ width: "100%", height: 132, marginTop: 2 }}>
                <Traza d={m.d} p={trazo} color={activo ? "#FFD23C" : "#9fb0d8"} w={activo ? 11 : 8} />
              </svg>
              <div style={{ fontWeight: 800, fontSize: 31, lineHeight: 1.05, color: activo ? "#fff" : "#10142a" }}>{m.tit}</div>
              <div style={{ fontWeight: 600, fontSize: 24, color: activo ? "#FFD23C" : "#7d85a0", marginTop: 2 }}>{m.sub}</div>
            </div>
          );
        })}
      </div>
    </>
  );
};

const Spinner: React.FC<{ size: number; spin: number }> = ({ size, spin }) => (
  <svg width={size} height={size} viewBox="-100 -100 200 200" style={{ transform: `rotate(${spin}deg)` }}>
    <defs>
      <radialGradient id="sg" cx="35%" cy="30%"><stop offset="0" stopColor="#7FB0FF" /><stop offset="1" stopColor="#1B4DFF" /></radialGradient>
    </defs>
    {[0, 120, 240].map((a) => (
      <g key={a} transform={`rotate(${a})`}>
        <rect x="-16" y="-64" width="32" height="64" rx="16" fill="url(#sg)" />
        <circle cx="0" cy="-64" r="30" fill="url(#sg)" />
        <circle cx="0" cy="-64" r="14" fill="#fff" opacity=".9" />
      </g>
    ))}
    <circle r="26" fill="#0b0b0d" />
    <circle r="12" fill="#cfd6e6" />
  </svg>
);

const PanelSpinner: React.FC<{ from: number }> = ({ from }) => {
  const t = useT();
  const p = pop(t, from + 0.5, 0.6);
  return (
    <>
      <Rotulo>¿TE ACORDÁS DE ESTO?</Rotulo>
      <div style={{ display: "flex", alignItems: "center", gap: 28, marginTop: 4 }}>
        <div style={{ transform: `scale(${p})`, filter: "drop-shadow(0 26px 30px rgba(20,40,120,.3))" }}>
          <Spinner size={330} spin={(t - from) * 560} />
        </div>
        <div>
          <Gold size={104} stroke={9}>EL SPINNER</Gold>
          <div style={{ fontWeight: 800, fontSize: 38, color: "#10142a", marginTop: 14, lineHeight: 1.1 }}>
            Se vendió como loco<br />y nadie supo por qué
          </div>
        </div>
      </div>
    </>
  );
};

// ======================================================================
// ESCENA DE FLUJO a pantalla completa: la persona sale del plano y el
// concepto se explica con etapas encadenadas por flechas que se dibujan.
// `orientacion`: "vertical" (etapas apiladas) · "horizontal" (línea de tiempo).
// ======================================================================
type Etapa = { at: number; icono: string; titulo: string; sub?: string; etiqueta?: string };

const Fondo: React.FC<{ p: number; children: React.ReactNode }> = ({ p, children }) => (
  <AbsoluteFill style={{ opacity: p, background: "radial-gradient(circle at 50% 36%,#ffffff 0%,#e9eefb 55%,#c9d4f0 100%)", fontFamily: INTER, color: "#10142a" }}>
    {children}
  </AbsoluteFill>
);

/** Flecha que se dibuja sola; `dir` 1 = hacia abajo, 0 = hacia la derecha. */
const FlechaDibujada: React.FC<{ p: number; vertical?: boolean; largo?: number; color?: string }> = ({
  p, vertical = true, largo = 92, color = NARANJA,
}) => {
  const cabeza = Math.max(0, (p - 0.72) / 0.28);
  return vertical ? (
    <svg width={120} height={largo} viewBox={`0 0 120 ${largo}`} style={{ overflow: "visible" }}>
      <path d={`M58,4 C76,${largo * 0.3} 44,${largo * 0.5} 60,${largo - 24}`} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p / 0.72)} />
      <polygon points={`60,${largo} 42,${largo - 30} 78,${largo - 30}`} fill={color} opacity={cabeza} transform={`scale(${0.6 + 0.4 * cabeza})`} style={{ transformOrigin: `60px ${largo - 12}px` }} />
    </svg>
  ) : (
    <svg width={largo} height={120} viewBox={`0 0 ${largo} 120`} style={{ overflow: "visible" }}>
      <path d={`M4,62 C${largo * 0.3},44 ${largo * 0.5},76 ${largo - 24},60`} fill="none" stroke={color} strokeWidth={10} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - Math.min(1, p / 0.72)} />
      <polygon points={`${largo},60 ${largo - 30},42 ${largo - 30},78`} fill={color} opacity={cabeza} transform={`scale(${0.6 + 0.4 * cabeza})`} style={{ transformOrigin: `${largo - 12}px 60px` }} />
    </svg>
  );
};

const Flujo: React.FC<{
  from: number;
  to: number;
  titulo: string[];
  etapas: Etapa[];
  orientacion?: "vertical" | "horizontal";
  remate?: { at: number; icono: string; texto: string };
}> = ({ from, to, titulo, etapas, orientacion = "vertical", remate }) => {
  const t = useT();
  if (t < from - 0.05 || t > to + 0.3) return null;
  const vert = orientacion === "vertical";
  const pIn = prog(t, from, 0.32);
  const pOut = 1 - prog(t, to, 0.28);
  const pRemate = remate ? pop(t, remate.at, 0.5) : 0;
  return (
    <Fondo p={pIn * pOut}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 238, display: "flex", flexDirection: "column", alignItems: "center", gap: 0 }}>
        {titulo.map((l, i) => {
          const p = pop(t, from + 0.05 + i * 0.12, 0.45);
          return (
            <div key={l} style={{ opacity: p, transform: `translateY(${(1 - p) * -30}px)` }}>
              <Gold size={titulo.length > 1 ? 92 : 104} stroke={9}>{l}</Gold>
            </div>
          );
        })}
      </div>

      <div
        style={{
          position: "absolute", left: 0, right: 0, top: vert ? 470 : 700,
          display: "flex", flexDirection: vert ? "column" : "row",
          alignItems: "center", justifyContent: "center", gap: 0,
        }}
      >
        {etapas.map((e, i) => {
          const p = pop(t, e.at, 0.5);
          const pFlecha = prog(t, e.at + 0.42, 0.55);
          return (
            <React.Fragment key={e.titulo}>
              {i > 0 && (
                <div style={{ position: "relative", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                  <FlechaDibujada p={pFlecha} vertical={vert} largo={vert ? 86 : 120} />
                  {e.etiqueta && (
                    <div style={{ position: "absolute", top: vert ? "50%" : -14, left: vert ? 86 : 0, right: vert ? "auto" : 0, textAlign: "center", fontWeight: 800, fontSize: 34, color: NARANJA, opacity: pFlecha, whiteSpace: "nowrap" }}>
                      {e.etiqueta}
                    </div>
                  )}
                </div>
              )}
              <div
                style={{
                  display: "flex", flexDirection: vert ? "row" : "column", alignItems: "center",
                  gap: vert ? 26 : 12, width: vert ? 820 : 240,
                  padding: vert ? "16px 28px" : "20px 10px", borderRadius: 34,
                  background: "#fff", boxShadow: "0 22px 48px rgba(20,34,80,.16)", border: "3px solid #e3e9f7",
                  transform: `translate${vert ? "X" : "Y"}(${(1 - p) * (vert ? (i % 2 ? 60 : -60) : 50)}px) scale(${0.82 + 0.18 * p}) rotate(${vert ? (1 - p) * (i % 2 ? 3 : -3) : 0}deg)`,
                  opacity: p, flexShrink: 0,
                }}
              >
                <Img
                  src={ic(e.icono)}
                  style={{
                    width: vert ? 132 : 156, height: vert ? 132 : 156, flexShrink: 0,
                    transform: `translateY(${Math.sin((t - e.at) * 4.4) * 5}px) rotate(${Math.sin((t - e.at) * 2.6) * 3}deg)`,
                    filter: "drop-shadow(0 12px 18px rgba(0,0,0,.28))",
                  }}
                />
                <div style={{ textAlign: vert ? "left" : "center" }}>
                  <div style={{ fontWeight: 800, fontSize: vert ? 50 : 60, letterSpacing: -1.5, lineHeight: 1.05 }}>{e.titulo}</div>
                  {e.sub && <div style={{ fontWeight: 600, fontSize: vert ? 32 : 28, color: "#6c7694", marginTop: 4 }}>{e.sub}</div>}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {remate && (
        <div style={{ position: "absolute", left: 60, right: 60, top: vert ? 1420 : 1150, display: "flex", alignItems: "center", justifyContent: "center", gap: 18, opacity: pRemate, transform: `translateY(${(1 - pRemate) * 30}px)` }}>
          <Img src={ic(remate.icono)} style={{ width: 70, height: 70 }} />
          <div style={{ fontWeight: 800, fontSize: 46, letterSpacing: -1, textAlign: "center" }}>{remate.texto}</div>
        </div>
      )}
    </Fondo>
  );
};

/** Cierre a pantalla completa: la pregunta que deja el video. */
const Cierre: React.FC = () => {
  const t = useT();
  if (t < FINAL - 0.05) return null;
  const p = prog(t, FINAL, 0.35);
  const s = pop(t, FINAL + 0.15, 0.7);
  const q = prog(t, FINAL + 1.5, 0.5);
  return (
    <Fondo p={p}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 262, display: "flex", flexDirection: "column", alignItems: "center", gap: 2 }}>
        <Gold size={116} stroke={0} style={{ filter: "drop-shadow(0 7px 0 #0b0b0d)" }}>¿POR QUÉ SE</Gold>
        <Gold size={116} stroke={0} style={{ filter: "drop-shadow(0 7px 0 #0b0b0d)" }}>PUSO DE MODA?</Gold>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 660, display: "flex", justifyContent: "center", transform: `scale(${s})` }}>
        <div style={{ filter: "drop-shadow(0 40px 40px rgba(20,40,120,.35))" }}>
          <Spinner size={680} spin={(t - FINAL) * 420 * Math.max(0.25, 1.4 - (t - FINAL) * 0.4)} />
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1480, display: "flex", alignItems: "center", justifyContent: "center", gap: 16, opacity: q }}>
        <Img src={ic("red_question_mark")} style={{ width: 70, height: 70 }} />
        <div style={{ fontWeight: 800, fontSize: 54, letterSpacing: -1 }}>no tiene explicación</div>
      </div>
    </Fondo>
  );
};

// ---------- sonido ----------
const A = ESCENA_FLUJO_A[0], B = ESCENA_FLUJO_B[0];
const SFX: Sfx[] = [
  { at: 0.12, f: "impacto", v: 0.5 },
  ...BIGS.map((b) => ({ at: b.from, f: "pop" as const, v: 0.9 })),
  { at: 3.7, f: "swoosh", v: 0.6 }, { at: 4.2, f: "pop", v: 0.7 }, { at: 6.2, f: "pop", v: 0.7 }, { at: 8.0, f: "ding", v: 0.7 },
  // escena de flujo A
  { at: A, f: "swoosh", v: 0.6 },
  { at: A + 0.35, f: "pop", v: 0.8 }, { at: A + 1.75, f: "pop", v: 0.8 }, { at: A + 3.3, f: "pop", v: 0.8 }, { at: A + 4.6, f: "pop", v: 0.8 },
  { at: A + 5.3, f: "ding", v: 0.7 },
  // escena de flujo B
  { at: B, f: "swoosh", v: 0.6 },
  { at: B + 0.5, f: "pop", v: 0.8 }, { at: B + 1.35, f: "pop", v: 0.8 }, { at: B + 2.2, f: "pop", v: 0.8 },
  { at: B + 3.4, f: "ding", v: 0.7 },
  { at: 50.5, f: "brillo", v: 0.7 },
  { at: 52.9, f: "riser", v: 0.6 }, { at: 54.3, f: "impacto", v: 0.55 },
  { at: 17.5, f: "glitch", v: 0.35 }, { at: 38.1, f: "glitch", v: 0.35 },
];

export const Main: React.FC = () => {
  const t = useT();
  const bn = BN.some(([a, b]) => t >= a && t <= b);
  return (
    <AbsoluteFill style={{ background: "#0b0b0d" }}>
      <ConTransiciones list={TRANS}>
        <AbsoluteFill style={{ filter: bn ? "grayscale(1) contrast(1.16) brightness(1.1)" : "saturate(1.28) contrast(1.06) brightness(1.15)" }}>
          <DualCam keys={CAM} />
        </AbsoluteFill>
        {!bn && (
          <AbsoluteFill style={{ mixBlendMode: "soft-light", opacity: 0.5, background: "radial-gradient(circle at 16% 14%,rgba(255,80,60,.9),transparent 55%), radial-gradient(circle at 88% 72%,rgba(255,170,90,.7),transparent 50%)" }} />
        )}
        <Hook />
        <Panel from={3.4} to={8.9}><TresMetodos from={3.4} /></Panel>
        <Panel from={50.3} to={53.9} alto={470}><PanelSpinner from={50.3} /></Panel>
        <BigPhrase />

        {/* ESCENA 1: la cadena de un factor externo (él dice: tsunami → la gente necesita cosas) */}
        <Flujo
          from={ESCENA_FLUJO_A[0]}
          to={ESCENA_FLUJO_A[1]}
          titulo={["QUÉ PASA CUANDO", "PASA ALGO AFUERA"]}
          etapas={[
            { at: A + 0.35, icono: "water_wave", titulo: "Pasa algo de golpe", sub: "una pandemia, un tsunami" },
            { at: A + 1.75, icono: "shopping_cart", titulo: "La gente lo necesita", sub: "para sobrevivir" },
            { at: A + 3.3, icono: "package", titulo: "Ese producto se agota", sub: "no hay stock" },
            { at: A + 4.6, icono: "chart_increasing", titulo: "La demanda explota", sub: "de la nada" },
          ]}
          remate={{ at: A + 5.3, icono: "high_voltage", texto: "Eso es un factor extraordinario" }}
        />

        {/* ESCENA 2: por qué el Mundial es extraordinario y no estacional */}
        <Flujo
          from={ESCENA_FLUJO_B[0]}
          to={ESCENA_FLUJO_B[1]}
          orientacion="horizontal"
          titulo={["¿CADA CUÁNTO", "PASA EL MUNDIAL?"]}
          etapas={[
            { at: B + 0.5, icono: "soccer_ball", titulo: "2018" },
            { at: B + 1.35, icono: "soccer_ball", titulo: "2022", etiqueta: "4 años" },
            { at: B + 2.2, icono: "soccer_ball", titulo: "2026", etiqueta: "4 años" },
          ]}
          remate={{ at: B + 3.4, icono: "calendar", texto: "No es del calendario: es extraordinario" }}
        />

        <Cierre />
      </ConTransiciones>
      <Look />
      <Subs />
      <Sounds list={[...SFX, ...sfxDeTransiciones(TRANS)]} />
    </AbsoluteFill>
  );
};

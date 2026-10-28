// Prueba de estilo: reel vertical "creador pro" (título dorado condensado, subtítulos blancos con frases
// en dorado + íconos azules brillantes, tarjetas flotantes inclinadas, flashes, blanco y negro por tramos).
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { loadFont as loadAnton } from "@remotion/google-fonts/Anton";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { DURATION, WORDS } from "./words";
import { Sfx, Sounds, useT, pop, prog } from "./lib";
import { ConTransiciones, Look, Transicion, sfxDeTransiciones } from "./fx";
import { CamKeyV, CamV, CAM_FULL } from "./reel";

const { fontFamily: ANTON } = loadAnton("normal", { weights: ["400"], subsets: ["latin"] });
const { fontFamily: INTER } = loadInter("normal", { weights: ["600", "800"], subsets: ["latin"] });

export const CTA_SECONDS = 0;

const GOLD = "linear-gradient(180deg,#FFF0A6 0%,#FFD23C 38%,#F2A900 72%,#B97800 100%)";
const BLUE_GLOW = "0 0 70px rgba(70,130,255,.75)";

// ---------- cámara: punch-ins en seco ----------
const z = (at: number, zoom: number): CamKeyV => ({ at, box: CAM_FULL, zoom, fy: 40 });
const CAM: CamKeyV[] = [
  z(0, 1.0), z(2.9, 1.2), z(5.8, 1.0), z(9.0, 1.16), z(12.0, 1.0), z(14.3, 1.22), z(17.4, 1.0), z(19.8, 1.18),
  z(22.8, 1.0), z(25.4, 1.24), z(28.8, 1.0), z(30.9, 1.18), z(34.0, 1.0), z(35.5, 1.26), z(38.1, 1.0),
  z(41.2, 1.2), z(45.0, 1.0), z(47.5, 1.22), z(49.4, 1.0), z(50.2, 1.2), z(53.4, 1.0),
];

// transiciones en los cambios de idea (flash, zoom con desenfoque, latigazo…)
const TRANS: Transicion[] = [
  { at: 2.9, tipo: "flash" }, { at: 9.0, tipo: "zoom" }, { at: 14.3, tipo: "desenfoque" }, { at: 19.8, tipo: "flash" },
  { at: 25.4, tipo: "latigo" }, { at: 30.9, tipo: "zoom" }, { at: 35.5, tipo: "sacudida" }, { at: 41.2, tipo: "flash" },
  { at: 47.5, tipo: "desenfoque" }, { at: 54.2, tipo: "flash" },
];

// tramos en blanco y negro (énfasis)
const BN: [number, number][] = [[17.4, 19.7], [38.1, 41.1]];

// ---------- frases grandes con ícono ----------
type Big = { from: number; to: number; lines: string[]; icon: string };
const BIGS: Big[] = [
  { from: 0.88, to: 2.6, lines: ["FACTORES", "EXTRAORDINARIOS"], icon: "iconos/high_voltage_3d.png" },
  { from: 9.14, to: 10.6, lines: ["UNA PANDEMIA"], icon: "iconos/microbe_3d.png" },
  { from: 12.62, to: 14.1, lines: ["UN TSUNAMI"], icon: "iconos/water_wave_3d.png" },
  { from: 25.52, to: 27.0, lines: ["EL MUNDIAL"], icon: "iconos/soccer_ball_3d.png" },
  { from: 29.26, to: 30.6, lines: ["CADA 4 AÑOS"], icon: "iconos/calendar_3d.png" },
  { from: 35.5, to: 37.0, lines: ["CIERTA", "INTUICIÓN"], icon: "iconos/brain_3d.png" },
  { from: 47.5, to: 49.2, lines: ["MÁS DIFÍCIL", "DE EXPLICAR"], icon: "iconos/red_question_mark_3d.png" },
  { from: 50.2, to: 51.6, lines: ["EL SPINNER"], icon: "iconos/cyclone_3d.png" },
];
const SCENE: [number, number] = [54.2, DURATION + 1];

// ---------- piezas ----------
const Gold: React.FC<{ children: React.ReactNode; size: number; skew?: number; stroke?: number; style?: React.CSSProperties }> = ({
  children, size, skew = -8, stroke = 12, style,
}) => (
  <div style={{ position: "relative", display: "inline-block", fontFamily: ANTON, fontSize: size, lineHeight: 0.98, transform: `skewX(${skew}deg)`, letterSpacing: 1, ...style }}>
    <span style={{ position: "absolute", inset: 0, color: "#0b0b0d", WebkitTextStroke: `${stroke}px #0b0b0d`, filter: "drop-shadow(0 10px 18px rgba(0,0,0,.55))" }}>{children}</span>
    <span style={{ position: "relative", background: GOLD, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent" }}>{children}</span>
  </div>
);

const Hook: React.FC = () => {
  const t = useT();
  if (t > 3.3) return null;
  const lines = ["EL MÉTODO", "QUE CASI", "NADIE USA"];
  return (
    <div style={{ position: "absolute", left: 56, top: 215, display: "flex", flexDirection: "column", gap: 4 }}>
      {lines.map((l, i) => {
        const p = pop(t, 0.12 + i * 0.16, 0.45);
        const out = prog(t, 2.9, 0.3);
        return (
          <div key={l} style={{ transform: `translateX(${(1 - p) * -90 - out * 140}px) scale(${0.85 + 0.15 * p})`, opacity: p * (1 - out), transformOrigin: "left center" }}>
            <Gold size={176}>{l}</Gold>
          </div>
        );
      })}
    </div>
  );
};

// Ícono 3D (assets/iconos3d → public/iconos con scripts/iconos.py sugerir). Rebota al entrar y flota.
const IconBadge: React.FC<{ icon: string; at: number; size?: number }> = ({ icon, at, size = 210 }) => {
  const t = useT();
  const p = pop(t, at, 0.5);
  const bob = Math.sin((t - at) * 5) * 6;
  return (
    <Img
      src={staticFile(icon)}
      style={{
        width: size, height: size, flexShrink: 0,
        transform: `translateY(${bob}px) scale(${p}) rotate(${(1 - p) * -25 + Math.sin((t - at) * 3) * 3}deg)`,
        filter: `drop-shadow(0 16px 24px rgba(0,0,0,.45)) drop-shadow(${BLUE_GLOW.replace("0 0 70px", "0 0 40px")})`,
      }}
    />
  );
};

const BigPhrase: React.FC = () => {
  const t = useT();
  const b = BIGS.find((x) => t >= x.from - 0.05 && t <= x.to + 0.2);
  if (!b) return null;
  const out = 1 - prog(t, b.to, 0.2);
  const p = pop(t, b.from, 0.4);
  return (
    <div style={{ position: "absolute", left: 40, right: 40, top: 1040, display: "flex", alignItems: "center", justifyContent: "center", gap: 26, opacity: out }}>
      <IconBadge icon={b.icon} at={b.from} />
      <div style={{ transform: `scale(${0.7 + 0.3 * p})`, opacity: p, transformOrigin: "left center", display: "flex", flexDirection: "column", gap: 2 }}>
        {b.lines.map((l) => (
          <Gold key={l} size={b.lines.length > 1 ? 104 : 124} stroke={10}>{l}</Gold>
        ))}
      </div>
    </div>
  );
};

// subtítulos normales: grupos de hasta 3 palabras, blancos, sin caja
type Chunk = { s: number; e: number; text: string };
const CHUNKS: Chunk[] = (() => {
  const out: Chunk[] = [];
  let cur: typeof WORDS = [];
  const flush = () => {
    if (!cur.length) return;
    out.push({ s: cur[0].s, e: cur[cur.length - 1].e, text: cur.map((w) => w.w).join(" ") });
    cur = [];
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
  if (t >= SCENE[0] - 0.05) return null;
  if (BIGS.some((b) => t >= b.from - 0.02 && t <= b.to + 0.15)) return null;
  const c = CHUNKS.find((x) => t >= x.s && t < x.e);
  if (!c) return null;
  const p = pop(t, c.s, 0.18);
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: 1170, textAlign: "center", pointerEvents: "none" }}>
      <span
        style={{
          fontFamily: INTER, fontWeight: 800, fontSize: 70, letterSpacing: -2.5, color: "#fff", display: "inline-block",
          transform: `scale(${0.9 + 0.1 * p})`, textShadow: "0 3px 6px rgba(0,0,0,.55), 0 0 24px rgba(0,0,0,.45)",
        }}
      >
        {c.text}
      </span>
    </div>
  );
};

// tarjeta blanca inclinada que "vuela" sobre la cabeza
const FloatCard: React.FC<{ from: number; to: number; x: number; y: number; rot: number; w?: number; children: React.ReactNode }> = ({
  from, to, x, y, rot, w = 440, children,
}) => {
  const t = useT();
  if (t < from - 0.05 || t > to + 0.4) return null;
  const p = pop(t, from, 0.55);
  const out = prog(t, to, 0.3);
  const bob = Math.sin((t - from) * 2.4) * 8;
  return (
    <div
      style={{
        position: "absolute", left: x, top: y + bob, width: w, padding: "28px 30px 30px", background: "#fff", borderRadius: 34,
        boxShadow: "0 40px 80px rgba(0,0,0,.45), 0 0 0 2px rgba(0,0,0,.04)", transform: `rotate(${rot + (1 - p) * 18}deg) scale(${(0.5 + 0.5 * p) * (1 - out * 0.2)})`,
        opacity: p * (1 - out), fontFamily: INTER, color: "#0b0b0d",
      }}
    >
      {children}
    </div>
  );
};

const Spinner: React.FC<{ size: number; spin: number; color?: string }> = ({ size, spin, color = "#1B4DFF" }) => (
  <svg width={size} height={size} viewBox="-100 -100 200 200" style={{ transform: `rotate(${spin}deg)` }}>
    <defs>
      <radialGradient id="sg" cx="35%" cy="30%"><stop offset="0" stopColor="#7FB0FF" /><stop offset="1" stopColor={color} /></radialGradient>
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

const Cards: React.FC = () => {
  const t = useT();
  return (
    <>
      <FloatCard from={9.3} to={12.5} x={560} y={250} rot={7}>
        <div style={{ fontWeight: 800, fontSize: 26, letterSpacing: 2, color: "#5a6070" }}>DEMANDA</div>
        <svg width="380" height="170" viewBox="0 0 380 170">
          <polyline points="8,150 70,140 120,148 180,100 240,110 300,40 365,14" fill="none" stroke="#1B4DFF" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
          <polygon points="365,14 335,16 358,42" fill="#1B4DFF" />
        </svg>
        <div style={{ fontWeight: 800, fontSize: 40, marginTop: 4, display: "flex", alignItems: "center", gap: 10 }}>se dispara <Img src={staticFile("iconos/chart_increasing_3d.png")} style={{ width: 54, height: 54 }} /></div>
      </FloatCard>
      <FloatCard from={50.3} to={53.7} x={540} y={240} rot={-8} w={430}>
        <div style={{ display: "flex", justifyContent: "center" }}>
          <Spinner size={300} spin={(t - 50.3) * 520} />
        </div>
        <div style={{ fontWeight: 800, fontSize: 40, textAlign: "center", marginTop: 8 }}>moda viral</div>
      </FloatCard>
    </>
  );
};

// etiqueta de vidrio abajo
const Chip: React.FC = () => {
  const t = useT();
  const from = 29.4, to = 33.2;
  if (t < from - 0.05 || t > to + 0.4) return null;
  const p = pop(t, from, 0.5);
  const out = prog(t, to, 0.3);
  return (
    <div
      style={{
        position: "absolute", left: 90, right: 90, top: 1400, padding: "26px 36px", borderRadius: 30, background: "rgba(20,22,30,.62)",
        border: "1.5px solid rgba(255,255,255,.18)", backdropFilter: "blur(18px)", display: "flex", alignItems: "center", gap: 24,
        transform: `translateY(${(1 - p) * 60}px)`, opacity: p * (1 - out), fontFamily: INTER, color: "#fff",
      }}
    >
      <Img src={staticFile("iconos/soccer_ball_3d.png")} style={{ width: 84, height: 84 }} />
      <div>
        <div style={{ fontWeight: 800, fontSize: 40, letterSpacing: -1 }}>Pasa 1 vez cada 4 años</div>
        <div style={{ fontWeight: 600, fontSize: 28, opacity: 0.7 }}>factor extraordinario</div>
      </div>
    </div>
  );
};

// escena a pantalla completa (fondo claro, ilustración animada)
const FullScene: React.FC = () => {
  const t = useT();
  if (t < SCENE[0] - 0.05) return null;
  const p = prog(t, SCENE[0], 0.4);
  const s = pop(t, SCENE[0] + 0.15, 0.7);
  return (
    <AbsoluteFill style={{ opacity: p, background: "radial-gradient(circle at 50% 38%,#ffffff 0%,#e6ecfb 60%,#cfd9f3 100%)" }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 250, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
        <Gold size={128} stroke={0} style={{ filter: "drop-shadow(0 8px 0 #0b0b0d)" }}>¿POR QUÉ SE</Gold>
        <Gold size={128} stroke={0} style={{ filter: "drop-shadow(0 8px 0 #0b0b0d)" }}>PUSO DE MODA?</Gold>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 640, display: "flex", justifyContent: "center", transform: `scale(${s})` }}>
        <div style={{ filter: "drop-shadow(0 40px 40px rgba(20,40,120,.35))" }}>
          <Spinner size={720} spin={(t - SCENE[0]) * 420 * Math.max(0.3, 1.4 - (t - SCENE[0]) * 0.35)} />
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1500, textAlign: "center", fontFamily: INTER, fontWeight: 800, fontSize: 52, color: "#1a2350", letterSpacing: -1 }}>
        no tiene explicación
      </div>
    </AbsoluteFill>
  );
};

// ---------- sonido ----------
const SFX: Sfx[] = [
  { at: 0.15, f: "impacto", v: 0.5 },
  ...BIGS.map((b) => ({ at: b.from, f: "pop" as const, v: 0.9 })),
  { at: 9.3, f: "ding", v: 0.6 }, { at: 29.4, f: "pop" }, { at: 50.3, f: "brillo", v: 0.7 },
  { at: 52.8, f: "riser", v: 0.6 },
  { at: 17.4, f: "glitch", v: 0.4 }, { at: 38.1, f: "glitch", v: 0.4 },
  { at: 14.3, f: "boom", v: 0.4 }, { at: 35.5, f: "boom", v: 0.5 }, { at: 47.5, f: "boom", v: 0.4 },
];

export const Main: React.FC = () => {
  const t = useT();
  const bn = BN.some(([a, b]) => t >= a && t <= b);
  return (
    <AbsoluteFill style={{ background: "#0b0b0d" }}>
      <ConTransiciones list={TRANS}>
        <AbsoluteFill style={{ filter: bn ? "grayscale(1) contrast(1.15) brightness(1.1)" : "saturate(1.3) contrast(1.07) brightness(1.16)" }}>
          <CamV keys={CAM} until={DURATION} />
        </AbsoluteFill>
        {!bn && (
          <AbsoluteFill style={{ mixBlendMode: "soft-light", opacity: 0.55, background: "radial-gradient(circle at 15% 12%,rgba(255,80,60,.9),transparent 55%), radial-gradient(circle at 90% 70%,rgba(255,170,90,.7),transparent 50%)" }} />
        )}
        <Hook />
        <Cards />
        <Chip />
        <BigPhrase />
        <FullScene />
      </ConTransiciones>
      <Look />
      <Subs />
      <Sounds list={[...SFX, ...sfxDeTransiciones(TRANS)]} />
    </AbsoluteFill>
  );
};

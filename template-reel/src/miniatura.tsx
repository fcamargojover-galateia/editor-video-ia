// Miniatura (YouTube 1280x720) o portada de reel (1080x1920). Se renderiza con scripts/extras.py --miniatura.
// La foto sale de los mejores fotogramas del video (public/miniatura_N.jpg).
import React from "react";
import { AbsoluteFill, Img, staticFile, useVideoConfig } from "remotion";
import { C, TITLE, MARCA } from "./theme";

export type MiniProps = { titulo: string; destacar?: string; foto: string; chip?: string };

export const Miniatura: React.FC<MiniProps> = ({ titulo, destacar, foto, chip }) => {
  const { width, height } = useVideoConfig();
  const vertical = height > width;
  const words = titulo.split(" ");
  const size = vertical ? 118 : words.length > 5 ? 92 : 112;
  const norm = (w: string) => w.replace(/[^\wáéíóúñü]/gi, "").toLowerCase();
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <Img
        src={staticFile(foto)}
        style={{
          position: "absolute",
          height: "100%",
          width: vertical ? "100%" : "62%",
          right: 0,
          objectFit: "cover",
          objectPosition: "50% 30%",
          filter: "contrast(1.08) saturate(1.12)",
        }}
      />
      <AbsoluteFill
        style={{
          background: vertical
            ? "linear-gradient(180deg, rgba(11,10,16,.85) 0%, rgba(11,10,16,0) 38%, rgba(11,10,16,0) 62%, rgba(11,10,16,.9) 100%)"
            : `linear-gradient(90deg, ${C.bg} 30%, rgba(11,10,16,.6) 52%, rgba(11,10,16,0) 72%)`,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: vertical ? 70 : 64,
          right: vertical ? 70 : "44%",
          top: vertical ? 250 : 0,
          bottom: vertical ? undefined : 0,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          gap: 22,
        }}
      >
        {chip && (
          <div style={{ alignSelf: "flex-start", background: C.violet, color: "#fff", fontFamily: TITLE, fontWeight: 900, fontSize: vertical ? 44 : 34, padding: "8px 22px", borderRadius: 12, textTransform: "uppercase" }}>
            {chip}
          </div>
        )}
        <div style={{ fontFamily: TITLE, fontWeight: 900, fontSize: size, lineHeight: 0.98, letterSpacing: -2, color: C.text, textTransform: "uppercase", WebkitTextStroke: "3px #000", paintOrder: "stroke fill", textShadow: "0 8px 0 rgba(0,0,0,.5)" }}>
          {words.map((w, i) => {
            const hit = destacar && norm(w) === norm(destacar);
            return (
              <span key={i} style={hit ? { color: C.bg, background: C.lime, padding: "0 12px", borderRadius: 12, WebkitTextStroke: "0", display: "inline-block", transform: "rotate(-2deg)" } : undefined}>
                {w}{" "}
              </span>
            );
          })}
        </div>
      </div>
      {!vertical && (
        <div style={{ position: "absolute", left: 64, bottom: 34, fontFamily: TITLE, fontWeight: 800, fontSize: 26, letterSpacing: 2, color: "rgba(255,255,255,.7)" }}>{MARCA.handle}</div>
      )}
    </AbsoluteFill>
  );
};

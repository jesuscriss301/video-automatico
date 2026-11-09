import React from "react";
import {
  AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig, Easing,
} from "remotion";
import datos from "./datos.json";
import { TX, Lang } from "./textos";

// Paleta de la skill brand-guidelines, una escena con cada color
const C = { dark: "#141413", light: "#faf9f5", mid: "#b0aea5", lgray: "#e8e6dc", orange: "#d97757", blue: "#6a9bcc", green: "#788c5d", ink2: "#5e5d59", card2: "#262624", line2: "#3a3a37" };
const POP = "Poppins, Arial, sans-serif";
const LORA = "Lora, Georgia, serif";
const SOLAPE = 24; // cuadros en que la escena nueva se abre en círculo sobre la anterior

const useS = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (delay = 0, cfg: object = { damping: 16, stiffness: 110, mass: 0.8 }) => spring({ frame: f - delay, fps, config: cfg });
};

const Entra: React.FC<{ d?: number; y?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({ d = 0, y = 70, style, children }) => {
  const s = useS()(d);
  return <div style={{ ...style, opacity: Math.min(1, s * 1.4), transform: `translateY(${(1 - s) * y}px) scale(${0.96 + 0.04 * s})` }}>{children}</div>;
};

// Iconos de trazo que se dibujan solos (pathLength = 1)
const PATHS: Record<string, string[]> = {
  casa: ["M3 10.5 12 3l9 7.5", "M5 9.5V21h14V9.5", "M10 21v-6h4v6"],
  portales: ["M5 4h14a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z", "M3 9h18", "M8 21h8", "M12 18v3"],
  billete: ["M4 6h16a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2z", "M12 9.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5z"],
  chat: ["M21 12a8 8 0 0 1-11.6 7.1L4 20.5l1.4-5A8 8 0 1 1 21 12z", "M9 11h6M9 14h4"],
  check: ["M5 12.5 10 17l9-10"],
  reloj: ["M12 3a9 9 0 1 1 0 18 9 9 0 0 1 0-18z", "M12 7v5l3 2"],
  regalo: ["M4.5 8h15A1.5 1.5 0 0 1 21 9.5V21H3V9.5A1.5 1.5 0 0 1 4.5 8z", "M3 12h18M12 8v13", "M12 8c-2-4-6-4-6-1.5S9 8 12 8zm0 0c2-4 6-4 6-1.5S15 8 12 8z"],
  estrella: ["m12 3 2.8 5.7 6.2.9-4.5 4.4 1 6.2-5.5-2.9-5.5 2.9 1-6.2L3 9.6l6.2-.9z"],
  flecha: ["M12 4v15", "m6 13 6 6 6-6"],
  usuario: ["M12 4a4 4 0 1 1 0 8 4 4 0 0 1 0-8z", "M4 21c0-4 4-6 8-6s8 2 8 6"],
  plano: ["M2 10 12 2l10 8", "M4 8.5V20h16V8.5", "M10 20v-6h4v6", "M6 11h3v3H6z", "M15 11h3v3h-3z"],
};
const Ico: React.FC<{ n: string; size: number; color: string; d?: number; dur?: number; w?: number }> = ({ n, size, color, d = 0, dur = 22, w = 1.8 }) => {
  const f = useCurrentFrame();
  const p = interpolate(f - d, [0, dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round">
      {PATHS[n].map((dd, i) => <path key={i} d={dd} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} />)}
    </svg>
  );
};

// texto con *resaltado*: entra palabra por palabra
const Frase: React.FC<{ t: string; acc: string; color: string; d?: number; paso?: number; style?: React.CSSProperties }> = ({ t, acc, color, d = 0, paso = 3, style }) => {
  const s = useS();
  let on = false;
  const palabras: { w: string; a: boolean }[] = [];
  t.split(" ").forEach((w) => {
    const ini = w.startsWith("*");
    if (ini) on = true;
    const a = on;
    if (w.replace(/[.?!,]+$/, "").endsWith("*")) on = false;
    palabras.push({ w: w.split("*").join(""), a });
  });
  return (
    <div style={style}>
      {palabras.map((p, i) => {
        const k = s(d + i * paso, { damping: 14, stiffness: 140 });
        return (
          <span key={i} style={{ display: "inline-block", marginRight: "0.26em", color: p.a ? acc : color, opacity: Math.min(1, k * 1.5), transform: `translateY(${(1 - k) * 40}px)` }}>
            {p.w}
          </span>
        );
      })}
    </div>
  );
};

// Fondo de cada escena: se abre en círculo desde un punto, encima de la anterior
const Escena: React.FC<{ bg: string; x?: number; y?: number; children: React.ReactNode }> = ({ bg, x = 50, y = 50, children }) => {
  const f = useCurrentFrame();
  const r = interpolate(f, [0, SOLAPE], [0, 150], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  return (
    <AbsoluteFill style={{ background: bg, clipPath: `circle(${r}% at ${x}% ${y}%)` }}>
      {children}
    </AbsoluteFill>
  );
};

const Flota: React.FC<{ amp?: number; per?: number; children: React.ReactNode }> = ({ amp = 6, per = 40, children }) => {
  const f = useCurrentFrame();
  return <div style={{ transform: `translateY(${Math.sin(f / per) * amp}px)` }}>{children}</div>;
};

const Tag: React.FC<{ t: string; color: string }> = ({ t, color }) => (
  <Entra d={2} y={20} style={{ position: "absolute", top: 230, left: 0, right: 0, textAlign: "center", fontFamily: POP, fontWeight: 700, fontSize: 30, letterSpacing: "0.18em", color }}>{t}</Entra>
);

// ---------------- escenas
const Gancho: React.FC<{ L: any; g: string; dur: number }> = ({ L, g, dur }) => {
  const f = useCurrentFrame();
  const s = useS();
  let vis: React.ReactNode = null;
  if (g === "a") {
    vis = (
      <div style={{ position: "absolute", top: 360, left: 0, right: 0, height: 480 }}>
        {[0, 1, 2, 3, 4].map((i) => {
          const k = s(4 + i * 5, { damping: 13, stiffness: 120 });
          const x = interpolate(k, [0, 1], [0, (i - 2) * 125]);
          const rot = interpolate(k, [0, 1], [0, (i - 2) * 5]);
          return (
            <div key={i} style={{ position: "absolute", left: 330, top: 20, width: 420, height: 400, background: C.card2, border: `2px solid ${C.line2}`, borderRadius: 28, padding: 22,
              boxShadow: "0 30px 60px rgba(0,0,0,.4)", transform: `translateX(${x}px) rotate(${rot}deg) translateY(${Math.abs(i - 2) * 22 * k}px)`, opacity: Math.min(1, k * 2) }}>
              <div style={{ height: 220, borderRadius: 16, background: `linear-gradient(135deg, ${[C.blue, C.green, C.orange, C.blue, C.green][i]}, ${C.card2})`, marginBottom: 18 }} />
              <div style={{ fontFamily: POP, fontWeight: 700, fontSize: 36, color: C.orange }}>{L.portal} {i + 1}</div>
              <div style={{ fontFamily: LORA, fontSize: 28, color: C.mid }}>{L.ficha}</div>
            </div>
          );
        })}
      </div>
    );
  } else if (g === "b") {
    const p = interpolate(f, [6, Math.min(dur * 0.8, 100)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
    vis = (
      <div style={{ position: "absolute", left: 340, top: 360, width: 400, height: 400 }}>
        <svg width={400} height={400} viewBox="0 0 100 100">
          <circle cx={50} cy={50} r={44} fill="none" stroke={C.line2} strokeWidth={5} />
          <circle cx={50} cy={50} r={44} fill="none" stroke={C.orange} strokeWidth={5} strokeLinecap="round" pathLength={1} strokeDasharray={1} strokeDashoffset={1 - p} transform="rotate(-90 50 50)" />
        </svg>
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: POP, fontWeight: 800, fontSize: 160, color: C.light, transform: `scale(${0.8 + 0.2 * s(8)})` }}>
          7<span style={{ fontSize: 46, color: C.mid, marginTop: 70, marginLeft: 8 }}>min</span>
        </div>
      </div>
    );
  } else {
    vis = <div style={{ position: "absolute", left: 300, top: 330 }}><Ico n="plano" size={480} color={C.orange} w={0.7} dur={34} d={4} /></div>;
  }
  return (
    <Escena bg={C.dark}>
      <Tag t={L.tag} color={C.orange} />
      {vis}
      <Frase t={L.ganchos[g]} acc={C.orange} color={C.light} d={10} paso={3}
        style={{ position: "absolute", top: 900, left: 80, right: 80, textAlign: "center", fontFamily: POP, fontWeight: 800, fontSize: 86, lineHeight: 1.1 }} />
    </Escena>
  );
};

const Contexto: React.FC<{ L: any }> = ({ L }) => (
  <Escena bg={C.light} x={0} y={100}>
    <Entra d={8} style={{ position: "absolute", left: 90, right: 90, top: 420 }}>
      <Flota><div style={{ background: "#fff", borderRadius: 32, padding: 44, display: "flex", gap: 36, alignItems: "center", boxShadow: "0 30px 70px rgba(20,20,19,.10)" }}>
        <div style={{ width: 150, height: 150, borderRadius: "50%", background: C.lgray, display: "flex", alignItems: "center", justifyContent: "center", flex: "none" }}>
          <Ico n="usuario" size={90} color={C.blue} d={14} w={2} />
        </div>
        <div>
          <div style={{ fontFamily: POP, fontWeight: 700, fontSize: 54, color: C.dark }}>{L.quien}</div>
          <div style={{ fontFamily: LORA, fontSize: 34, color: C.ink2 }}>{L.rol}</div>
        </div>
      </div></Flota>
    </Entra>
    <Entra d={20} style={{ position: "absolute", left: 90, right: 90, top: 760 }}>
      <Flota per={46}><div style={{ background: "#fff", borderRadius: 32, padding: 44, boxShadow: "0 30px 70px rgba(20,20,19,.10)" }}>
        <div style={{ height: 330, borderRadius: 20, marginBottom: 30, backgroundColor: "#f3f1ea",
          backgroundImage: `linear-gradient(${C.lgray} 2px, transparent 2px), linear-gradient(90deg, ${C.lgray} 2px, transparent 2px)`, backgroundSize: "54px 54px",
          display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Ico n="plano" size={260} color={C.blue} d={28} dur={40} w={0.9} />
        </div>
        <div style={{ fontFamily: POP, fontWeight: 700, fontSize: 50, color: C.dark }}>{L.estado}</div>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 8, fontFamily: LORA, fontStyle: "italic", fontSize: 36, color: C.ink2 }}>
          <span style={{ width: 18, height: 18, borderRadius: "50%", background: C.green }} />{L.estado2}
        </div>
      </div></Flota>
    </Entra>
  </Escena>
);

const Funciones: React.FC<{ L: any; dur: number }> = ({ L, dur }) => {
  const s = useS();
  const icos = ["casa", "portales", "billete", "chat"];
  const cols = [C.orange, C.blue, C.green, C.orange];
  return (
    <Escena bg={C.lgray} x={100} y={0}>
      <Frase t={L.pregunta} acc={C.dark} color={C.dark} d={6} paso={2}
        style={{ position: "absolute", top: 330, left: 80, right: 80, textAlign: "center", fontFamily: POP, fontWeight: 800, fontSize: 74, lineHeight: 1.1 }} />
      {L.funciones.map((t: string, i: number) => {
        const marca = 30 + i * Math.round((dur * 0.6) / 4);
        const k = s(marca, { damping: 12, stiffness: 160 });
        return (
          <Entra key={i} d={14 + i * 5} style={{ position: "absolute", left: 90, right: 90, top: 600 + i * 232 }}>
            <div style={{ height: 200, background: "#fff", borderRadius: 30, display: "flex", alignItems: "center", gap: 34, padding: "0 40px",
              border: `3px solid ${k > 0.5 ? C.green : "transparent"}`, boxShadow: "0 20px 50px rgba(20,20,19,.08)", transform: `scale(${1 + 0.03 * Math.sin(Math.min(1, k) * Math.PI)})` }}>
              <Ico n={icos[i]} size={80} color={cols[i]} d={18 + i * 5} />
              <span style={{ fontFamily: POP, fontWeight: 700, fontSize: 48, color: C.dark }}>{t}</span>
              <div style={{ marginLeft: "auto", width: 76, height: 76, borderRadius: 20, border: `3px solid ${C.mid}`, background: k > 0.05 ? C.green : "transparent",
                display: "flex", alignItems: "center", justifyContent: "center", transform: `scale(${0.85 + 0.15 * k})` }}>
                {k > 0.05 && <Ico n="check" size={54} color={C.light} d={marca} dur={10} w={2.6} />}
              </div>
            </div>
          </Entra>
        );
      })}
    </Escena>
  );
};

const Encuesta: React.FC<{ L: any; dur: number }> = ({ L, dur }) => {
  const f = useCurrentFrame();
  const w = interpolate(f, [10, dur * 0.85], [6, 64], { extrapolateRight: "clamp", easing: Easing.inOut(Easing.quad) });
  return (
    <Escena bg={C.blue} x={0} y={0}>
      <Entra d={8} style={{ position: "absolute", left: 90, right: 90, top: 420 }}>
        <Flota amp={5}><div style={{ background: C.light, borderRadius: 34, padding: 50, boxShadow: "0 40px 80px rgba(20,20,19,.25)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontFamily: POP, fontWeight: 800, fontSize: 58, color: C.dark }}>{L.encTit}</span>
            <span style={{ display: "flex", alignItems: "center", gap: 10, fontFamily: POP, fontWeight: 700, fontSize: 40, color: C.dark }}>
              <Ico n="reloj" size={48} color={C.orange} d={12} />{L.encMin}
            </span>
          </div>
          <div style={{ height: 16, borderRadius: 8, background: C.lgray, margin: "30px 0 40px", overflow: "hidden" }}>
            <div style={{ width: `${w}%`, height: "100%", borderRadius: 8, background: C.orange }} />
          </div>
          <div style={{ fontFamily: LORA, fontWeight: 600, fontSize: 44, color: C.dark, marginBottom: 28, lineHeight: 1.25 }}>{L.encQ}</div>
          {L.encOps.map((o: string, i: number) => (
            <Entra key={i} d={18 + i * 5} y={30}>
              <div style={{ display: "flex", alignItems: "center", gap: 24, padding: "26px 28px", borderRadius: 20, marginBottom: 16, fontFamily: POP, fontWeight: 500, fontSize: 40, color: C.dark,
                border: `3px solid ${i === 0 ? C.orange : C.lgray}`, background: i === 0 ? "rgba(217,119,87,.10)" : "transparent" }}>
                <span style={{ width: 40, height: 40, borderRadius: "50%", border: `3px solid ${i === 0 ? C.orange : C.mid}`, background: i === 0 ? `radial-gradient(${C.orange} 45%, transparent 50%)` : "none", flex: "none" }} />
                {o}
              </div>
            </Entra>
          ))}
        </div></Flota>
      </Entra>
    </Escena>
  );
};

const Fundadores: React.FC<{ L: any }> = ({ L }) => {
  const f = useCurrentFrame();
  const brillo = 0.25 + 0.15 * Math.sin(f / 12);
  const items = [["regalo", C.blue], ["estrella", C.orange]];
  return (
    <Escena bg={C.dark} x={100} y={100}>
      {L.fund.map(([a, b]: string[], i: number) => (
        <Entra key={i} d={8 + i * 14} style={{ position: "absolute", left: 90, right: 90, top: 470 + i * 400 }}>
          <Flota per={38 + i * 8}><div style={{ background: C.card2, borderRadius: 32, padding: 48, display: "flex", gap: 38, alignItems: "center",
            border: `3px solid ${items[i][1]}`, boxShadow: i ? `0 0 80px rgba(217,119,87,${brillo})` : "none" }}>
            <Ico n={items[i][0]} size={120} color={items[i][1]} d={14 + i * 14} dur={26} />
            <div>
              <div style={{ fontFamily: POP, fontWeight: 800, fontSize: 60, color: C.light }}>{a}</div>
              <div style={{ fontFamily: LORA, fontSize: 40, color: i ? C.light : C.mid, lineHeight: 1.25 }}>{b}</div>
            </div>
          </div></Flota>
        </Entra>
      ))}
    </Escena>
  );
};

const Cta: React.FC<{ L: any }> = ({ L }) => {
  const f = useCurrentFrame();
  return (
    <Escena bg={C.orange} x={50} y={100}>
      <Frase t={L.cta1} acc={C.dark} color={C.dark} d={6} paso={3}
        style={{ position: "absolute", top: 560, left: 80, right: 80, textAlign: "center", fontFamily: POP, fontWeight: 800, fontSize: 100, lineHeight: 1.05 }} />
      <Entra d={18} style={{ position: "absolute", left: 140, right: 140, top: 900 }}>
        <div style={{ background: C.dark, color: C.light, borderRadius: 999, padding: "34px 20px", textAlign: "center", fontFamily: POP, fontWeight: 700, fontSize: 52 }}>{L.cta2}</div>
      </Entra>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1090, display: "flex", justifyContent: "center", transform: `translateY(${Math.abs(Math.sin(f / 9)) * 26}px)` }}>
        <Ico n="flecha" size={150} color={C.dark} d={24} w={2.2} />
      </div>
      <Entra d={28} style={{ position: "absolute", left: 0, right: 0, top: 1310, textAlign: "center", fontFamily: LORA, fontStyle: "italic", fontSize: 44, color: C.dark }}>{L.cta3}</Entra>
    </Escena>
  );
};

const Logo: React.FC = () => {
  const f = useCurrentFrame();
  const s = useS();
  const k = s(4, { damping: 12, stiffness: 120 });
  const cursor = Math.floor(f / 10) % 2 === 0;
  return (
    <Escena bg={C.dark}>
      <AbsoluteFill style={{ alignItems: "center", justifyContent: "center", flexDirection: "column" }}>
        <div style={{ fontFamily: "JetBrains Mono, monospace", fontWeight: 800, fontSize: 230, color: C.orange, transform: `scale(${0.7 + 0.3 * k})`, opacity: Math.min(1, k * 2) }}>
          &gt;<span style={{ opacity: cursor ? 1 : 0.15 }}>_</span>
        </div>
        <Entra d={12} y={30}>
          <div style={{ fontFamily: POP, fontWeight: 700, fontSize: 76, color: C.light, marginTop: 10 }}>EasyPro <span style={{ color: C.orange }}>Digital</span></div>
        </Entra>
        <Entra d={20} y={20}>
          <div style={{ fontFamily: LORA, fontSize: 38, color: C.mid, marginTop: 14 }}>easyprodigital.com</div>
        </Entra>
      </AbsoluteFill>
    </Escena>
  );
};

// ---------------- subtítulos
const Subs: React.FC<{ subs: { text: string; from: number; dur: number }[] }> = ({ subs }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sub = subs.find((x) => f >= x.from && f < x.from + x.dur);
  if (!sub) return null;
  const k = spring({ frame: f - sub.from, fps, config: { damping: 14, stiffness: 200 } });
  return (
    <div style={{ position: "absolute", top: 1590, left: 0, right: 0, textAlign: "center" }}>
      <span style={{ display: "inline-block", maxWidth: 940, padding: "10px 28px 14px", borderRadius: 18, background: "rgba(20,20,19,.88)", color: C.light,
        fontFamily: POP, fontWeight: 700, fontSize: 60, lineHeight: 1.15, transform: `scale(${0.88 + 0.12 * k})`, opacity: Math.min(1, k * 2) }}>
        {sub.text.split(" ").map((w, i) => <span key={i} style={{ color: /\d|WhatsApp/.test(w) ? C.orange : C.light }}>{w} </span>)}
      </span>
    </div>
  );
};

export const Video: React.FC<{ id: string }> = ({ id }) => {
  const d = (datos as any)[id];
  const L = TX[d.lang as Lang];
  const total = d.total;
  const fin = (e: any) => Math.min(e.dur + SOLAPE, total - e.from);
  const pantalla = (e: any) => {
    switch (e.id) {
      case "gancho": return <Gancho L={L} g={d.gancho} dur={e.dur} />;
      case "contexto": return <Contexto L={L} />;
      case "funciones": return <Funciones L={L} dur={e.dur} />;
      case "encuesta": return <Encuesta L={L} dur={e.dur} />;
      case "fundadores": return <Fundadores L={L} />;
      case "cta": return <Cta L={L} />;
      default: return <Logo />;
    }
  };
  return (
    <AbsoluteFill style={{ background: C.dark }}>
      {d.escenas.map((e: any) => (
        <Sequence key={e.id} from={e.from} durationInFrames={fin(e)}>{pantalla(e)}</Sequence>
      ))}
      <Subs subs={d.subs} />
      {d.audios.map((a: any, i: number) => (
        <Sequence key={`v${i}`} from={a.from}><Audio src={staticFile(a.src)} /></Sequence>
      ))}
      {d.escenas.slice(1).map((e: any, i: number) => (
        <Sequence key={`fx${i}`} from={Math.max(0, e.from - 3)} durationInFrames={30}>
          <Audio src={staticFile(e.id === "logo" ? "sparkle.mp3" : i % 2 ? "whoosh.mp3" : "whoosh-short.mp3")} volume={0.2} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

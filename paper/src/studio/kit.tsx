// The studio kit: a lit grey ruled backdrop seen through a moving 3D camera, and the objects his reference
// reels put on it (pinned notes, Claude's app, documents, a numbered arc, kinetic lines, the comment pill).
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {FPS} from './data';
import {C, SANS, SERIF, clamp, ease, easeIO, mix, pop} from './style';

// ---------- camera ----------

// World point (x, y) at the centre of the screen, zoom z, then tilts in degrees.
export type Cam = {x: number; y: number; z: number; rx?: number; ry?: number; rz?: number};
// A key marked 'lin' is reached at constant speed (for camera paths sampled densely, like a pan that
// follows words); the others ease in and out.
export type Key = [number, Cam] | [number, Cam, 'lin'];

const lerpCam = (a: Cam, b: Cam, k: number): Cam => ({
  x: mix(a.x, b.x, k),
  y: mix(a.y, b.y, k),
  z: a.z * Math.pow(b.z / a.z, k),   // zoom eases in log space, so a push-in feels even
  rx: mix(a.rx ?? 0, b.rx ?? 0, k),
  ry: mix(a.ry ?? 0, b.ry ?? 0, k),
  rz: mix(a.rz ?? 0, b.rz ?? 0, k),
});

// Keys are [second, camera]; the camera eases from each key to the next and holds outside them.
export const track = (t: number, keys: Key[]): Cam => {
  if (t <= keys[0][0]) return keys[0][1];
  for (let i = 0; i + 1 < keys.length; i++) {
    const [t0, a] = keys[i];
    const [t1, b, lin] = keys[i + 1];
    if (t < t1) return lerpCam(a, b, lin ? clamp((t - t0) / (t1 - t0)) : easeIO(t, t0, t1));
  }
  return keys[keys.length - 1][1];
};

// A slow hand-held float, like his camera never quite stops.
const drift = (c: Cam, t: number): Cam => ({
  ...c,
  x: c.x + 7 * Math.sin(t * 0.63),
  y: c.y + 6 * Math.sin(t * 0.47 + 1.3),
  rz: (c.rz ?? 0) + 0.3 * Math.sin(t * 0.41 + 0.4),
});

const Ruled: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: -3600,
      top: -3600,
      width: 7200,
      height: 7200,
      background: C.plane,
      backgroundImage: `repeating-linear-gradient(180deg, transparent 0px, transparent 81px, ${C.rule} 81px, ${C.rule} 83px, rgba(255,255,255,0.42) 83px, rgba(255,255,255,0.42) 84px)`,
    }}
  />
);

// The set: ruled plane plus children, seen through the camera, with motion blur along fast moves.
export const World: React.FC<{t: number; keys: Key[]; id: string; children?: React.ReactNode}> = ({t, keys, id, children}) => {
  const c = drift(track(t, keys), t);
  const p = drift(track(t - 1 / FPS, keys), t - 1 / FPS);
  // only fast moves smear (over 8 px a frame on screen); slow pushes and the float stay sharp
  const sx = clamp((Math.abs(c.x - p.x) * c.z - 8) * 0.3, 0, 22);
  const sy = clamp((Math.abs(c.y - p.y) * c.z - 8) * 0.3, 0, 22);
  const sz = clamp((Math.abs(Math.log(c.z / p.z)) - 0.02) * 200, 0, 8);
  const blur = Math.max(sx, sy, sz) > 0.6;
  return (
    <AbsoluteFill style={{overflow: 'hidden'}}>
      {blur && (
        <svg width="0" height="0" style={{position: 'absolute'}}>
          <filter id={id} x="-5%" y="-5%" width="110%" height="110%">
            <feGaussianBlur stdDeviation={`${(sx + sz).toFixed(2)} ${(sy + sz).toFixed(2)}`} />
          </filter>
        </svg>
      )}
      <AbsoluteFill style={{perspective: 2300, perspectiveOrigin: '540px 960px', filter: blur ? `url(#${id})` : undefined}}>
        <div
          style={{
            position: 'absolute',
            left: 540,
            top: 960,
            width: 0,
            height: 0,
            transformStyle: 'preserve-3d',
            transform: `rotateX(${c.rx}deg) rotateY(${c.ry}deg) rotateZ(${c.rz}deg) scale(${c.z}) translate(${-c.x}px, ${-c.y}px)`,
          }}
        >
          <Ruled />
          {children}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

// Screen-space finish over every set: soft focus at the edges, then his vignette. Stops fitted to his
// frames (brightness 231 in the middle, 143 at the side edges, 137 near the top, 78 then 47 at the bottom).
const V = (a: number) => `rgba(22,19,24,${a})`;
export const Lens: React.FC = () => (
  <>
    <AbsoluteFill
      style={{
        backdropFilter: 'blur(4px)',
        WebkitMaskImage: 'radial-gradient(ellipse 60% 48% at 50% 47%, transparent 60%, black 100%)',
        maskImage: 'radial-gradient(ellipse 60% 48% at 50% 47%, transparent 60%, black 100%)',
      }}
    />
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 700px 970px at 540px 900px, ${V(0)} 0%, ${V(0.11)} 30%, ${V(0.22)} 50%, ${V(0.4)} 75%, ${V(0.52)} 95%, ${V(0.62)} 120%), linear-gradient(180deg, ${V(0)} 60%, ${V(0.23)} 75%, ${V(0.43)} 90%, ${V(0.6)} 100%)`,
      }}
    />
  </>
);

// ---------- placing things ----------

// Centred on world (x, y); `z` lifts it toward the camera, rot/rx/ry tilt it.
export const Place: React.FC<{x: number; y: number; z?: number; rot?: number; rx?: number; ry?: number; style?: React.CSSProperties; children?: React.ReactNode}> = ({x, y, z = 0, rot = 0, rx = 0, ry = 0, style, children}) => (
  <div
    style={{
      position: 'absolute',
      left: x,
      top: y,
      transform: `translate(-50%, -50%) translateZ(${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotate(${rot}deg)`,
      ...style,
    }}
  >
    {children}
  </div>
);

// His entrance: rises, sharpens and settles with a small overshoot.
export const enter = (t: number, t0: number, rise = 46, stiff = 210): React.CSSProperties => {
  const k = pop(t, t0, stiff);
  return {
    opacity: clamp(k * 1.6),
    transform: `translateY(${(1 - k) * rise}px) scale(${mix(0.88, 1, k)})`,
    filter: k < 0.98 ? `blur(${((1 - clamp(k)) * 9).toFixed(2)}px)` : undefined,
  };
};

// ---------- pinned notes ----------

const Pin: React.FC = () => (
  <div style={{position: 'absolute', left: '50%', top: 34, width: 0, height: 0}}>
    <div style={{position: 'absolute', left: -2, top: 18, width: 40, height: 16, borderRadius: '50%', background: 'rgba(60,24,20,0.3)', filter: 'blur(5px)'}} />
    <div style={{position: 'absolute', left: -4, top: 6, width: 8, height: 22, borderRadius: 4, background: 'linear-gradient(90deg,#9a9a9e,#d8d8dc)', transform: 'rotate(18deg)'}} />
    <div
      style={{
        position: 'absolute',
        left: -27,
        top: -30,
        width: 54,
        height: 54,
        borderRadius: '50%',
        background: 'radial-gradient(circle at 36% 30%, #FFA585 0%, #F05A33 42%, #C1361B 100%)',
        boxShadow: '0 7px 12px rgba(120,30,10,0.32), inset 0 -3px 5px rgba(90,10,0,0.25)',
      }}
    />
  </div>
);

export const Check: React.FC<{size?: number; color?: string; stroke?: string}> = ({size = 64, color = C.orange, stroke = '#fff'}) => (
  <div style={{width: size, height: size, borderRadius: '50%', background: color, display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 8px 18px rgba(150,70,40,0.3)'}}>
    <svg width={size * 0.56} height={size * 0.56} viewBox="0 0 24 24">
      <path d="M4.5 12.5l4.8 4.8L19.5 7" fill="none" stroke={stroke} strokeWidth={3.4} strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  </div>
);

// A frosted card pinned to the board, a peach card inside it: "01" and the step's title.
export const Note: React.FC<{n: string; title: string; done?: number}> = ({n, title, done = 0}) => (
  <div style={{position: 'relative', width: 410, height: 440}}>
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: 34,
        background: 'linear-gradient(170deg, rgba(255,255,255,0.86), rgba(244,242,246,0.7))',
        border: '2px solid rgba(255,255,255,0.95)',
        boxShadow: '0 44px 70px rgba(30,24,34,0.26), 0 10px 20px rgba(30,24,34,0.12)',
      }}
    />
    <div
      style={{
        position: 'absolute',
        left: 34,
        right: 34,
        top: 92,
        bottom: 38,
        borderRadius: 20,
        background: `linear-gradient(165deg, #FCF0E7 0%, ${C.peach} 100%)`,
        boxShadow: 'inset 0 1px 0 rgba(255,255,255,0.9)',
        padding: '24px 26px',
        fontFamily: SANS,
      }}
    >
      <div style={{color: C.orange, fontSize: 36, fontWeight: 500, letterSpacing: '-0.02em'}}>{n}</div>
      <div style={{color: C.ink, fontSize: 44, fontWeight: 700, lineHeight: 1.02, letterSpacing: '-0.045em', marginTop: 8, whiteSpace: 'pre-line'}}>{title}</div>
      <div style={{marginTop: 22, height: 9, width: '80%', borderRadius: 5, background: 'rgba(130,80,55,0.13)'}} />
      <div style={{marginTop: 12, height: 9, width: '58%', borderRadius: 5, background: 'rgba(130,80,55,0.13)'}} />
    </div>
    <Pin />
    {done > 0 && (
      <div style={{position: 'absolute', right: -18, top: 70, transform: `scale(${done})`, opacity: clamp(done * 2)}}>
        <Check />
      </div>
    )}
  </div>
);

export const Heading: React.FC<{size?: number; children?: React.ReactNode}> = ({size = 70, children}) => (
  <div style={{fontFamily: SANS, fontWeight: 700, fontSize: size, letterSpacing: '-0.05em', lineHeight: 1.0, color: C.ink, textAlign: 'center', whiteSpace: 'pre'}}>
    {children}
  </div>
);

// ---------- Claude's app ----------

const RAYS = [0, 29, 60, 91, 119, 151, 180, 211, 240, 271, 299, 331];
const LENS = [44, 37, 46, 39, 45, 36, 44, 39, 46, 37, 45, 40];
export const Starburst: React.FC<{size: number; color?: string; spin?: number}> = ({size, color = C.orange, spin = 0}) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{display: 'block', transform: `rotate(${spin}deg)`}}>
    {RAYS.map((a, i) => {
      const r = (a * Math.PI) / 180;
      return <line key={i} x1={Math.cos(r) * 6} y1={Math.sin(r) * 6} x2={Math.cos(r) * LENS[i]} y2={Math.sin(r) * LENS[i]} stroke={color} strokeWidth={10} strokeLinecap="round" />;
    })}
  </svg>
);

export const Greeting: React.FC<{text: string; spin?: number}> = ({text, spin = 0}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 22, whiteSpace: 'nowrap'}}>
    <Starburst size={66} spin={spin} />
    <div style={{fontFamily: SERIF, fontWeight: 400, fontSize: 72, letterSpacing: '-0.025em', color: C.claudeText}}>{text}</div>
  </div>
);

const Arrow: React.FC<{size?: number; color?: string}> = ({size = 30, color = '#fff'}) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path d="M12 19V5M5.5 11.5L12 5l6.5 6.5" fill="none" stroke={color} strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

// The prompt box: attachments on top, the text (or the placeholder), + on the left, model and send on the right.
export const InputBox: React.FC<{w?: number; text?: string; caret?: boolean; attach?: React.ReactNode; press?: number}> = ({w = 760, text, caret, attach, press = 0}) => (
  <div
    style={{
      width: w,
      borderRadius: 32,
      background: C.card,
      border: `1.5px solid ${C.cardLine}`,
      boxShadow: '0 22px 60px rgba(30,25,35,0.13), 0 3px 8px rgba(30,25,35,0.06)',
      padding: '26px 28px 22px',
      fontFamily: SANS,
    }}
  >
    {attach && <div style={{display: 'flex', gap: 16, marginBottom: 20}}>{attach}</div>}
    <div style={{fontSize: 31, color: text ? C.claudeText : '#A6A29B', letterSpacing: '-0.012em', minHeight: 42, whiteSpace: 'nowrap'}}>
      {text || 'How can I help you today?'}
      {caret && <span style={{display: 'inline-block', width: 3, height: 34, marginLeft: 3, background: C.claudeText, verticalAlign: '-6px'}} />}
    </div>
    <div style={{display: 'flex', alignItems: 'center', marginTop: 28}}>
      <div style={{width: 54, height: 54, borderRadius: 15, border: `1.5px solid ${C.cardLine}`, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6E6A63', fontSize: 36, fontWeight: 400, lineHeight: 1}}>+</div>
      <div style={{flex: 1}} />
      <div style={{fontSize: 25, color: '#6E6A63', marginRight: 24, letterSpacing: '-0.01em'}}>Opus 5.5</div>
      <div style={{width: 60, height: 60, borderRadius: 17, background: C.orange, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${1 - 0.12 * press})`}}>
        <Arrow />
      </div>
    </div>
  </div>
);

export const Chips: React.FC<{items: string[]}> = ({items}) => (
  <div style={{display: 'flex', gap: 14, fontFamily: SANS}}>
    {items.map((x) => (
      <div key={x} style={{padding: '11px 22px', borderRadius: 16, border: `1.5px solid ${C.cardLine}`, background: 'rgba(255,255,255,0.55)', fontSize: 25, color: '#5E5A54', letterSpacing: '-0.01em'}}>
        {x}
      </div>
    ))}
  </div>
);

export const FileChip: React.FC<{name: string; kind?: string}> = ({name, kind = 'PDF'}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 16, padding: '13px 24px 13px 13px', borderRadius: 18, background: '#F7F5F1', border: `1.5px solid ${C.cardLine}`, fontFamily: SANS, whiteSpace: 'nowrap'}}>
    <div style={{width: 54, height: 64, borderRadius: 9, background: '#E5484D', color: '#fff', fontWeight: 700, fontSize: 17, display: 'flex', alignItems: 'flex-end', justifyContent: 'center', paddingBottom: 9, letterSpacing: '0.02em'}}>{kind}</div>
    <div>
      <div style={{fontSize: 26, fontWeight: 600, color: C.claudeText, letterSpacing: '-0.02em'}}>{name}</div>
      <div style={{fontSize: 21, color: C.claudeMute, marginTop: 2}}>{kind}</div>
    </div>
  </div>
);

// A small candlestick chart card (made-up candles, only a picture of "a chart").
const rand = (seed: number) => {
  let s = seed;
  return () => ((s = (s * 16807) % 2147483647) / 2147483647);
};
export const ChartThumb: React.FC<{label: string; seed: number; trend: number; w?: number}> = ({label, seed, trend, w = 250}) => {
  const r = rand(seed);
  const n = 16;
  let p = 50;
  const candles = Array.from({length: n}, () => {
    const o = p;
    p = p + trend + (r() - 0.5) * 9;
    const hi = Math.max(o, p) + r() * 4;
    const lo = Math.min(o, p) - r() * 4;
    return {o, c: p, hi, lo};
  });
  const all = candles.flatMap((x) => [x.hi, x.lo]);
  const mn = Math.min(...all);
  const mx = Math.max(...all);
  const H = w * 0.52;
  const y = (v: number) => 8 + (1 - (v - mn) / (mx - mn)) * (H - 16);
  const cw = (w - 28) / n;
  return (
    <div style={{width: w, borderRadius: 18, background: C.card, border: `1.5px solid ${C.cardLine}`, padding: '12px 12px 10px', fontFamily: SANS, boxShadow: '0 6px 16px rgba(30,25,35,0.06)'}}>
      <svg width={w - 26} height={H}>
        {[0.25, 0.5, 0.75].map((g) => (
          <line key={g} x1={0} x2={w} y1={H * g} y2={H * g} stroke="#EEEBE6" strokeWidth={1.5} />
        ))}
        {candles.map((x, i) => {
          const up = x.c >= x.o;
          const col = up ? '#26A65B' : '#E5484D';
          const cx = i * cw + cw / 2;
          return (
            <g key={i}>
              <line x1={cx} x2={cx} y1={y(x.hi)} y2={y(x.lo)} stroke={col} strokeWidth={2} />
              <rect x={cx - cw * 0.32} width={cw * 0.64} y={y(Math.max(x.o, x.c))} height={Math.max(2, Math.abs(y(x.o) - y(x.c)))} fill={col} rx={1.5} />
            </g>
          );
        })}
      </svg>
      <div style={{fontSize: 23, fontWeight: 600, color: C.claudeText, marginTop: 6, letterSpacing: '-0.015em'}}>{label}</div>
    </div>
  );
};

export const UserBubble: React.FC<{children?: React.ReactNode}> = ({children}) => (
  <div style={{background: C.bubble, borderRadius: 28, padding: '20px 26px', fontFamily: SANS, fontSize: 30, color: C.claudeText, letterSpacing: '-0.012em', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 16, whiteSpace: 'nowrap'}}>
    {children}
  </div>
);

// Claude's answer: serif text like the app. `lines` appear at their times; a peach highlight reads down them.
export const Reply: React.FC<{t: number; title: string; titleAt: number; lines: {text: string; at: number}[]; w?: number; spin?: number}> = ({t, title, titleAt, lines, w = 860, spin = 0}) => (
  <div style={{width: w, fontFamily: SERIF, color: C.claudeText}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 16, ...enter(t, titleAt, 20)}}>
      <Starburst size={44} spin={spin} />
      <div style={{fontSize: 36, fontWeight: 600, letterSpacing: '-0.02em'}}>{title}</div>
    </div>
    <div style={{marginTop: 22}}>
      {lines.map((l, i) => {
        const sweep = ease(t, l.at + 0.05, l.at + 0.38);
        const hl = `rgba(236,150,104,${(0.42 * (1 - ease(t, l.at + 0.75, l.at + 1.1) * 0.75)).toFixed(3)})`;
        return (
          <div key={i} style={{display: 'flex', alignItems: 'baseline', gap: 16, fontSize: 36, lineHeight: 1.5, letterSpacing: '-0.012em', ...enter(t, l.at, 18, 260)}}>
            <div style={{width: 34, color: C.orange, fontFamily: SANS, fontWeight: 600, fontSize: 30}}>{i + 1}.</div>
            <span
              style={{
                backgroundImage: `linear-gradient(${hl}, ${hl})`,
                backgroundRepeat: 'no-repeat',
                backgroundSize: `${sweep * 100}% 78%`,
                backgroundPosition: '0 60%',
                padding: '0 4px',
              }}
            >
              {l.text}
            </span>
          </div>
        );
      })}
    </div>
  </div>
);

// Grey shimmering lines while Claude works.
export const Thinking: React.FC<{t: number; t0: number; label: string; spin?: number; w?: number}> = ({t, t0, label, spin = 0, w = 860}) => (
  <div style={{width: w, fontFamily: SERIF, color: C.claudeText, ...enter(t, t0, 20)}}>
    <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
      <Starburst size={44} spin={spin} />
      <div style={{fontSize: 34, color: C.claudeMute, fontStyle: 'normal', letterSpacing: '-0.015em'}}>{label}</div>
    </div>
    {[0.94, 0.82, 0.88, 0.6].map((f, i) => {
      const sh = ((t - t0) * 0.9 - i * 0.12) % 1;
      return (
        <div
          key={i}
          style={{
            marginTop: i ? 18 : 30,
            height: 22,
            width: `${f * 100}%`,
            borderRadius: 11,
            background: `linear-gradient(90deg, #E4E0D9 ${(sh - 0.2) * 100}%, #F3F0EB ${sh * 100}%, #E4E0D9 ${(sh + 0.2) * 100}%)`,
            opacity: clamp((t - t0 - 0.15 - i * 0.12) * 5),
          }}
        />
      );
    })}
  </div>
);

// ---------- documents ----------

const cellW = (r: () => number) => 38 + r() * 46;

// "10 years of financials": a white sheet, FY columns pop in at `cols` times, rows of grey figures fill in.
export const Sheet: React.FC<{t: number; title: string; titleAt: number; rows: string[]; years: string[]; cols: number[]}> = ({t, title, titleAt, rows, years, cols}) => {
  const r = rand(7);
  const widths = rows.map(() => years.map(() => cellW(r)));
  return (
    <div style={{width: 1180, background: C.card, borderRadius: 14, padding: '44px 46px 40px', fontFamily: SANS, boxShadow: '0 40px 80px rgba(30,24,34,0.22), 0 6px 14px rgba(30,24,34,0.08)'}}>
      <div style={{fontSize: 46, fontWeight: 700, color: C.ink, letterSpacing: '-0.045em', ...enter(t, titleAt, 16)}}>{title}</div>
      <div style={{height: 3, background: C.ink, marginTop: 18, marginBottom: 14, borderRadius: 2}} />
      <div style={{display: 'flex', alignItems: 'center', height: 54}}>
        <div style={{width: 230, fontSize: 21, color: C.inkSoft, fontWeight: 600, letterSpacing: '0.04em'}}>METRIC</div>
        {years.map((y, j) => (
          <div key={y} style={{width: 85, textAlign: 'center', fontSize: 22, fontWeight: 600, color: C.ink, ...enter(t, cols[j], 14, 320)}}>
            {y}
          </div>
        ))}
      </div>
      {rows.map((row, i) => (
        <div key={row} style={{display: 'flex', alignItems: 'center', height: 64, borderTop: '1.5px solid #ECE9E4'}}>
          <div style={{width: 230, fontSize: 27, fontWeight: 600, color: C.ink, letterSpacing: '-0.025em'}}>{row}</div>
          {years.map((y, j) => {
            const k = ease(t, cols[j] + 0.04 + i * 0.025, cols[j] + 0.3 + i * 0.025);
            return (
              <div key={y} style={{width: 85, display: 'flex', justifyContent: 'center'}}>
                <div style={{height: 11, width: widths[i][j] * k, borderRadius: 6, background: '#CFCBD2', opacity: k}} />
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
};

// The score sheet: each row a bar out of 10 (a picture of a score, no claim), then the overall rating
// with the line he draws at 6.
export const ScoreSheet: React.FC<{t: number; title: string; titleAt: number; rows: {label: string; v: number; at: number}[]}> = ({t, title, titleAt, rows}) => (
  <div style={{width: 900, background: C.card, borderRadius: 14, padding: '42px 46px 46px', fontFamily: SANS, boxShadow: '0 40px 80px rgba(30,24,34,0.22), 0 6px 14px rgba(30,24,34,0.08)'}}>
    <div style={{fontSize: 48, fontWeight: 700, color: C.ink, letterSpacing: '-0.045em', ...enter(t, titleAt, 16)}}>{title}</div>
    <div style={{height: 3, background: C.ink, marginTop: 18, marginBottom: 10, borderRadius: 2}} />
    {rows.map((row) => {
      const k = ease(t, row.at + 0.05, row.at + 0.55);
      return (
        <div key={row.label} style={{display: 'flex', alignItems: 'center', height: 76, borderBottom: '1.5px solid #ECE9E4', ...enter(t, row.at, 14, 300)}}>
          <div style={{width: 300, fontSize: 31, fontWeight: 600, color: C.ink, letterSpacing: '-0.03em'}}>{row.label}</div>
          <div style={{flex: 1, display: 'flex', gap: 8}}>
            {Array.from({length: 10}, (_, i) => (
              <div key={i} style={{flex: 1, height: 22, borderRadius: 6, background: i < Math.round(row.v * k) ? C.orange : '#ECE8E2'}} />
            ))}
          </div>
        </div>
      );
    })}
  </div>
);

// Overall rating out of 10: a track, his line at 6, a fill that crosses it (grey until it does, then orange).
export const Rating: React.FC<{t: number; t0: number; lineAt: number; fillFrom: number; fillTo: number; to: number}> = ({t, t0, lineAt, fillFrom, fillTo, to}) => {
  const f = to * easeIO(t, fillFrom, fillTo);
  const over = f > 0.6;
  const line = pop(t, lineAt, 260);
  return (
    <div style={{width: 900, fontFamily: SANS, ...enter(t, t0, 20)}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'baseline'}}>
        <div style={{fontSize: 38, fontWeight: 700, color: C.ink, letterSpacing: '-0.04em'}}>Rating</div>
        <div style={{fontSize: 26, color: C.inkSoft}}>out of 10</div>
      </div>
      <div style={{position: 'relative', height: 44, marginTop: 26, borderRadius: 22, background: '#D9D5DC', boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.08)'}}>
        <div style={{position: 'absolute', left: 0, top: 0, bottom: 0, width: `${f * 100}%`, borderRadius: 22, background: over ? C.orange : '#9C98A0'}} />
        <div style={{position: 'absolute', left: '60%', top: -26, bottom: -26, width: 5, marginLeft: -2.5, borderRadius: 3, background: C.ink, opacity: clamp(line * 1.5), transform: `scaleY(${line})`}} />
        <div
          style={{
            position: 'absolute',
            left: '60%',
            top: -104,
            transform: `translateX(-50%) scale(${line})`,
            opacity: clamp(line * 1.5),
            width: 78,
            height: 66,
            borderRadius: 14,
            background: C.ink,
            color: '#fff',
            fontSize: 42,
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          6
        </div>
      </div>
    </div>
  );
};

// A pill label with an optional check: white with ink text, or ink with white text (`dark`).
export const Pill: React.FC<{text: string; dark?: boolean; check?: boolean; size?: number}> = ({text, dark, check, size = 40}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: size * 0.35,
      padding: `${size * 0.36}px ${size * 0.7}px`,
      borderRadius: 999,
      background: dark ? C.ink : C.card,
      color: dark ? '#fff' : C.ink,
      fontFamily: SANS,
      fontWeight: 700,
      fontSize: size,
      letterSpacing: '-0.035em',
      whiteSpace: 'nowrap',
      boxShadow: '0 18px 36px rgba(30,24,34,0.22)',
    }}
  >
    {check && <Check size={size * 1.1} />}
    {text}
  </div>
);

// ---------- the numbered arc ----------

// A big thin arc; numbered dark discs ride it; each label wipes in left to right on its word.
export const ArcList: React.FC<{t: number; items: {label: string; at: number; dot: number}[]; R: number; gap: number}> = ({t, items, R, gap}) => {
  const ang = (i: number) => (i - (items.length - 1) / 2) * gap;
  return (
    <>
      <svg width={2 * R + 40} height={2 * R + 40} style={{position: 'absolute', left: -2 * R - 20, top: -R - 20, overflow: 'visible'}}>
        <circle cx={R + 20} cy={R + 20} r={R} fill="none" stroke="#3B393E" strokeWidth={3.5} />
      </svg>
      {items.map((it, i) => {
        const a = (ang(i) * Math.PI) / 180;
        const x = -R + R * Math.cos(a);
        const y = R * Math.sin(a);
        const d = pop(t, it.dot, 240);
        const wipe = ease(t, it.at, it.at + 0.55);
        return (
          <div key={i} style={{position: 'absolute', left: x, top: y, transform: 'translate(-50%, -50%)'}}>
            <div style={{width: 104, height: 104, borderRadius: '50%', background: C.dark, color: '#fff', fontFamily: SANS, fontWeight: 500, fontSize: 52, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: `scale(${d})`, boxShadow: '0 10px 22px rgba(20,18,22,0.25)'}}>
              {i + 1}
            </div>
            <div
              style={{
                position: 'absolute',
                left: 140,
                top: '50%',
                transform: 'translateY(-50%)',
                fontFamily: SANS,
                fontWeight: 500,
                fontSize: 66,
                lineHeight: 1.04,
                letterSpacing: '-0.04em',
                color: C.ink,
                whiteSpace: 'nowrap',
                opacity: d * 0.999,
                WebkitMaskImage: `linear-gradient(90deg, black ${wipe * 120 - 20}%, rgba(0,0,0,0.12) ${wipe * 120}%)`,
                maskImage: `linear-gradient(90deg, black ${wipe * 120 - 20}%, rgba(0,0,0,0.12) ${wipe * 120}%)`,
                filter: wipe > 0 && wipe < 1 ? `blur(${((1 - wipe) * 2.5).toFixed(2)}px)` : undefined,
              }}
            >
              {it.label}
            </div>
          </div>
        );
      })}
    </>
  );
};

// ---------- kinetic text ----------

// DM Sans advance widths (em), close enough to aim the camera; boxes hug the real text in the DOM.
const ADV: Record<string, number> = {' ': 0.26, i: 0.25, l: 0.25, j: 0.25, t: 0.36, f: 0.34, r: 0.38, I: 0.28, m: 0.86, w: 0.78, M: 0.86, W: 0.95};
export const textW = (s: string, size: number, track = -0.035) =>
  [...s].reduce((a, ch) => a + (ADV[ch] ?? (ch === ch.toUpperCase() && /[A-Z]/.test(ch) ? 0.66 : /[0-9]/.test(ch) ? 0.6 : 0.56)) + track, 0) * size;

export type KWord = {text: string; at: number; hl?: number; off?: number};

// One line of words that appear as he says them; `hl` puts the ink box on a word from that second (and
// `off` takes it away). Returns the x of each word's centre so the camera can follow.
export const kineticLayout = (words: KWord[], size: number) => {
  const gap = 0.26 * size;
  let x = 0;
  return words.map((w) => {
    const wd = textW(w.text, size) + (w.hl !== undefined ? 0.3 * size : 0);
    const c = x + wd / 2;
    x += wd + gap;
    return c;
  });
};

export const KineticLine: React.FC<{t: number; words: KWord[]; size: number; weight?: number}> = ({t, words, size, weight = 500}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: 0.26 * size, whiteSpace: 'nowrap', fontFamily: SANS, fontWeight: weight, fontSize: size, letterSpacing: '-0.035em', color: C.ink}}>
    {words.map((w, i) => {
      const k = ease(t, w.at, w.at + 0.16);
      const box = w.hl === undefined ? 0 : ease(t, w.hl, w.hl + 0.14);   // wipes on left to right
      const boxOn = w.off === undefined ? 1 : 1 - ease(t, w.off, w.off + 0.1);   // and fades off
      return (
        <span
          key={i}
          style={{
            position: 'relative',
            display: 'inline-block',
            padding: w.hl !== undefined ? `0 ${0.15 * size}px` : 0,
            opacity: k,
            transform: `translateY(${(1 - k) * 0.25 * size}px)`,
            filter: k < 1 ? `blur(${((1 - k) * 8).toFixed(2)}px)` : undefined,
            color: box * boxOn > 0.5 ? '#fff' : C.ink,
          }}
        >
          <span
            style={{
              position: 'absolute',
              left: 0,
              right: 0,
              top: '4%',
              bottom: '-2%',
              background: C.ink,
              borderRadius: size * 0.08,
              opacity: boxOn,
              transform: `scaleX(${box})`,
              transformOrigin: 'left center',
              zIndex: -1,
            }}
          />
          <span style={{position: 'relative'}}>{w.text}</span>
        </span>
      );
    })}
  </div>
);

// ---------- the comment pill (CTA) ----------

export const CommentPill: React.FC<{word: string; k: number}> = ({word, k}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 22,
      padding: '12px 14px 12px 40px',
      borderRadius: 999,
      background: '#fff',
      boxShadow: '0 10px 30px rgba(0,0,0,0.28)',
      transform: `scale(${mix(0.6, 1, k)})`,
      opacity: clamp(k * 1.8),
      fontFamily: SANS,
    }}
  >
    <div style={{fontSize: 60, fontWeight: 700, color: C.ink, letterSpacing: '-0.02em'}}>{word}</div>
    <div style={{width: 72, height: 72, borderRadius: '50%', background: C.ink, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
      <svg width={34} height={34} viewBox="0 0 24 24">
        <path d="M5 15l7-7 7 7" fill="none" stroke="#fff" strokeWidth={3.2} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  </div>
);

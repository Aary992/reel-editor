// His motion-graphic kit: paper, step header, Claude icon, macOS folder, dotted lines, white cards, checks.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C, FONT, mix} from './style';

const NOISE =
  "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='320' height='320'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.32  0 0 0 0 0.26  0 0 0 0 0.18  0 0 0 0.10 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")";

export const Paper: React.FC<{style?: React.CSSProperties}> = ({style}) => (
  <AbsoluteFill style={{background: C.paper, overflow: 'hidden', ...style}}>
    <AbsoluteFill
      style={{
        backgroundImage: `linear-gradient(${C.grid} 1.5px, transparent 1.5px), linear-gradient(90deg, ${C.grid} 1.5px, transparent 1.5px)`,
        backgroundSize: '54px 54px',
        backgroundPosition: '-2px -2px',
      }}
    />
    <AbsoluteFill style={{backgroundImage: NOISE}} />
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 45%, rgba(255,250,240,0.18) 0%, rgba(0,0,0,0) 55%, rgba(110,85,50,0.10) 100%)'}} />
  </AbsoluteFill>
);

export const StepHeader: React.FC<{n?: number; title: string; y: number; k: number; size?: number}> = ({n, title, y, k, size = 60}) => (
  <div
    style={{
      position: 'absolute',
      top: y,
      left: 0,
      right: 0,
      textAlign: 'center',
      fontFamily: FONT,
      fontWeight: 800,
      fontSize: size,
      letterSpacing: '-0.04em',
      opacity: k,
      transform: `translateY(${(1 - k) * 10}px)`,
    }}
  >
    {n !== undefined && <span style={{color: C.terracotta}}>Step {n}. </span>}
    <span style={{color: C.ink}}>{title}</span>
  </div>
);

// Claude's mark, drawn: uneven rounded rays around a small hub.
const RAYS = [0, 29, 60, 91, 119, 151, 180, 211, 240, 271, 299, 331];
const LENS = [44, 37, 46, 39, 45, 36, 44, 39, 46, 37, 45, 40];
export const Starburst: React.FC<{size: number; color: string; spin?: number}> = ({size, color, spin = 0}) => (
  <svg width={size} height={size} viewBox="-50 -50 100 100" style={{display: 'block', transform: `rotate(${spin}deg)`}}>
    {RAYS.map((a, i) => {
      const r = (a * Math.PI) / 180;
      return (
        <line key={i} x1={Math.cos(r) * 6} y1={Math.sin(r) * 6} x2={Math.cos(r) * LENS[i]} y2={Math.sin(r) * LENS[i]} stroke={color} strokeWidth={10} strokeLinecap="round" />
      );
    })}
  </svg>
);

export const ClaudeIcon: React.FC<{size: number; style?: React.CSSProperties}> = ({size, style}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: size * 0.24,
      background: 'linear-gradient(160deg, #E4876A 0%, #D46A4A 55%, #C55C3C 100%)',
      boxShadow: `inset 0 ${size * 0.025}px 0 rgba(255,255,255,0.35), inset 0 -${size * 0.03}px 0 rgba(0,0,0,0.12), 0 ${size * 0.06}px ${size * 0.14}px rgba(90,50,30,0.28)`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      ...style,
    }}
  >
    <Starburst size={size * 0.66} color="#FFFFFF" />
  </div>
);

export const Label: React.FC<{text: string; color?: string; size?: number; style?: React.CSSProperties}> = ({text, color = C.ink, size = 34, style}) => (
  <div style={{fontFamily: FONT, fontWeight: 800, fontSize: size, letterSpacing: '-0.035em', color, textAlign: 'center', whiteSpace: 'nowrap', ...style}}>{text}</div>
);

// macOS-style blue folder, tilted like his. `solid` 0..1 takes it from the pale ghost to the full folder;
// `open` drops the front flap; children sit between the back and the front (photos, papers).
export const Folder: React.FC<{w: number; solid?: number; open?: number; children?: React.ReactNode}> = ({w, solid = 1, open = 0, children}) => {
  const h = (w * 190) / 240;
  return (
    <div
      style={{
        position: 'relative',
        width: w,
        height: h,
        opacity: mix(0.4, 1, solid),
        filter: `saturate(${mix(0.25, 1, solid)}) brightness(${mix(1.18, 1, solid)}) drop-shadow(0 ${w * 0.04}px ${w * 0.05}px rgba(60,80,100,0.22))`,
        transform: 'perspective(1400px) rotateX(16deg) rotateY(-14deg) rotateZ(-5deg)',
      }}
    >
      <svg width={w} height={h} viewBox="0 0 240 190" style={{position: 'absolute', inset: 0}}>
        <path d="M14 20 Q14 10 24 10 H84 Q91 10 95 15 L103 25 H216 Q226 25 226 35 V170 Q226 180 216 180 H24 Q14 180 14 170 Z" fill={C.folderDeep} />
        <rect x="30" y="34" width="180" height="120" rx="4" fill="#F1F1EE" />
        <rect x="36" y="40" width="172" height="116" rx="4" fill="#FFFFFF" />
      </svg>
      <div style={{position: 'absolute', inset: 0}}>{children}</div>
      <svg
        width={w}
        height={h}
        viewBox="0 0 240 190"
        style={{position: 'absolute', inset: 0, transformOrigin: '50% 100%', transform: `scaleY(${1 - open * 0.22}) skewX(${-open * 14}deg)`}}
      >
        <defs>
          <linearGradient id="ff" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#8DD6F6" />
            <stop offset="1" stopColor={C.folder} />
          </linearGradient>
        </defs>
        <path d="M14 62 Q14 54 22 54 H218 Q226 54 226 62 V170 Q226 180 216 180 H24 Q14 180 14 170 Z" fill="url(#ff)" />
        <path d="M18 56.5 H222" stroke={C.folderLight} strokeWidth="3" strokeLinecap="round" />
        <path d="M24 166 H216" stroke="rgba(40,120,170,0.25)" strokeWidth="2" strokeLinecap="round" />
      </svg>
    </div>
  );
};

// Dotted terracotta line that draws itself (p 0..1), with an arrowhead once it lands.
export const DottedPath: React.FC<{d: string; p: number; w: number; h: number; color?: string; arrow?: {x: number; y: number; angle: number}; dot?: number}> = ({
  d,
  p,
  w,
  h,
  color = C.terracotta,
  arrow,
  dot = 6,
}) => {
  const id = React.useId().replace(/:/g, '');
  return (
    <svg width={w} height={h} style={{position: 'absolute', left: 0, top: 0, overflow: 'visible'}}>
      <defs>
        <mask id={`m${id}`} maskUnits="userSpaceOnUse" x="-100" y="-100" width={w + 200} height={h + 200}>
          <path d={d} pathLength={1} stroke="#fff" strokeWidth={dot * 3} fill="none" strokeDasharray="1 1" strokeDashoffset={1 - p} />
        </mask>
      </defs>
      <path d={d} stroke={color} strokeWidth={dot} strokeLinecap="round" fill="none" strokeDasharray={`0.1 ${dot * 2.4}`} mask={`url(#m${id})`} />
      {arrow && p >= 0.98 && (
        <path
          d="M -14 -12 L 0 0 L -14 12"
          transform={`translate(${arrow.x} ${arrow.y}) rotate(${arrow.angle})`}
          stroke={color}
          strokeWidth={dot * 0.8}
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
      )}
    </svg>
  );
};

export const Check: React.FC<{size: number; k?: number; color?: string}> = ({size, k = 1, color = C.terracotta}) => (
  <div
    style={{
      width: size,
      height: size,
      borderRadius: size,
      background: color,
      transform: `scale(${k})`,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      boxShadow: '0 4px 10px rgba(120,50,20,0.25)',
    }}
  >
    <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 24 24">
      <path d="M5 12.5 L10 17 L19 7" stroke="#fff" strokeWidth="3.4" strokeLinecap="round" strokeLinejoin="round" fill="none" />
    </svg>
  </div>
);

export const Card: React.FC<{style?: React.CSSProperties; children: React.ReactNode}> = ({style, children}) => (
  <div
    style={{
      background: C.card,
      borderRadius: 26,
      boxShadow: '0 2px 0 rgba(0,0,0,0.04), 0 18px 44px rgba(40,30,20,0.22)',
      border: `1.5px solid ${C.cardLine}`,
      overflow: 'hidden',
      fontFamily: FONT,
      ...style,
    }}
  >
    {children}
  </div>
);

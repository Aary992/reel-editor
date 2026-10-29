// The repo look, generic part: grey top panel with the beat's card, his talking head below, the blue hook
// title over the first sentence, pixel captions on the seam, sound effects. A new reel only needs beats.tsx.
import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {HOOK, SCENES, SFX} from './beats';
import {DURATION, FPS, WORDS, clipAt} from './data';
import {C, PIXEL, SANS, SEAM, pop} from './style';

const FACE_SCALE = 1.1;
const HAIR_Y = SEAM + 120; // his hair sits this far down the frame, under the caption

const sceneAt = (t: number) => {
  let i = 0;
  while (i + 1 < SCENES.length && t >= SCENES[i + 1].from - 1e-3) i++;
  return SCENES[i];
};

// Captions: UPPERCASE, up to 5 words / 24 characters, a new chunk after a comma or full stop. Each chunk
// stays up until the next one, like the reference (never an empty seam). None under the hook title.
const CHUNKS = (() => {
  const out: (typeof WORDS)[] = [];
  let cur: typeof WORDS = [];
  WORDS.filter((w) => w.s >= HOOK.to - 0.05).forEach((w, k, all) => {
    const prev = all[k - 1];
    const chars = cur.map((x) => x.w.trim()).join(' ').length + 1 + w.w.trim().length;
    if (cur.length && (cur.length >= 5 || chars > 24 || /[.,!?]$/.test(prev.w.trim()))) {
      out.push(cur);
      cur = [];
    }
    cur.push(w);
  });
  if (cur.length) out.push(cur);
  return out.map((c, k) => ({
    text: c.map((x) => x.w.trim()).join(' ').replace(/[.!?]$/, '').toUpperCase(),
    s: c[0].s,
    e: out[k + 1]?.[0].s ?? DURATION,
  }));
})();

const Panel: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: 0,
      top: 0,
      width: 1080,
      height: SEAM,
      background: C.panel,
      backgroundImage: `radial-gradient(${C.dot} 1.6px, transparent 1.8px)`,
      backgroundSize: '30px 30px',
    }}
  />
);

const Face: React.FC<{t: number}> = ({t}) => {
  const clip = clipAt(t);
  const w = 1080 * FACE_SCALE;
  const tx = Math.min(0, Math.max(1080 - w, 540 - clip.cx * w));
  const ty = HAIR_Y - clip.hair * 1920 * FACE_SCALE;
  return (
    <div style={{position: 'absolute', left: 0, top: SEAM, width: 1080, height: 1920 - SEAM, overflow: 'hidden'}}>
      <div style={{position: 'absolute', left: tx, top: ty - SEAM, width: w, height: 1920 * FACE_SCALE}}>
        <OffthreadVideo src={staticFile('repo/cut.mp4')} style={{width: '100%', height: '100%'}} />
      </div>
    </div>
  );
};

const Card: React.FC<{t: number}> = ({t}) => {
  const sc = sceneAt(t);
  const k = sc.pop === false ? 1 : Math.min(1.2, pop(t, sc.from));
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity: Math.min(1, k * 1.6),
        transform: `translateY(${(1 - k) * 26}px) scale(${0.95 + 0.05 * k})`,
        transformOrigin: `540px ${SEAM / 2}px`,
      }}
    >
      <sc.Card t={t} t0={sc.from} />
    </div>
  );
};

const Hook: React.FC<{t: number}> = ({t}) => {
  if (t >= HOOK.to) return null;
  return (
    <div style={{position: 'absolute', top: SEAM - 82, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
      <div
        style={{
          background: C.blue,
          color: '#fff',
          fontFamily: SANS,
          fontWeight: 700,
          fontSize: 62,
          lineHeight: 1.12,
          letterSpacing: '-0.01em',
          textAlign: 'center',
          padding: '18px 30px 22px',
        }}
      >
        {HOOK.lines.map((l) => (
          <div key={l}>{l}</div>
        ))}
      </div>
    </div>
  );
};

const Captions: React.FC<{t: number}> = ({t}) => {
  const c = CHUNKS.find((x) => t >= x.s && t < x.e);
  if (!c) return null;
  return (
    <div style={{position: 'absolute', top: SEAM + 8, left: 0, right: 0, display: 'flex', justifyContent: 'center'}}>
      <div
        style={{
          transform: 'translateY(-50%)',
          background: C.blue,
          color: C.lime,
          fontFamily: PIXEL,
          fontWeight: 400,
          fontSize: 50,
          letterSpacing: '0.02em',
          lineHeight: 1,
          padding: '16px 20px 14px',
          borderRadius: 6,
          whiteSpace: 'nowrap',
        }}
      >
        {c.text}
      </div>
    </div>
  );
};

export const Repo: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Panel />
      <Face t={t} />
      <Card t={t} />
      <Hook t={t} />
      <Captions t={t} />
      {SFX.map(([f, s, v], i) => (
        <Sequence key={i} from={Math.round(s * FPS)} durationInFrames={45} layout="none">
          <Audio src={staticFile(`repo/sfx/${f}.wav`)} volume={v} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

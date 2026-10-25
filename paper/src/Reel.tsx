// The paper look, generic part: his talking head in one of three layouts, the beat graphics from beats.tsx,
// captions, and the sound effects. A new reel only needs a new beats.tsx.
import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {Paper} from './art';
import {NAMES, SCENES, SFX} from './beats';
import {DURATION, FPS, WORDS, clipAt} from './data';
import {FONT, pop} from './style';

const SPLIT_SCALE = 1.0;

const sceneAt = (t: number) => {
  let i = 0;
  while (i + 1 < SCENES.length && t >= SCENES[i + 1].from - 1e-3) i++;
  return {i, ...SCENES[i]};
};

// Captions: 1 to 3 words, lowercase like his (names, "I" and ALL CAPS words stay), a new chunk at
// punctuation, pauses and scene changes, never carried over into the next scene.
const keep = (w: string) => NAMES.includes(w) || /^I('|$)/.test(w) || (w.length > 1 && w === w.toUpperCase() && /[A-Z]/.test(w));
const CHUNKS = (() => {
  const out: (typeof WORDS)[] = [];
  let cur: typeof WORDS = [];
  WORDS.forEach((w, k) => {
    const prev = WORDS[k - 1];
    const chars = cur.map((x) => x.w.trim()).join(' ').length + w.w.trim().length;
    const crossed = prev && sceneAt(prev.s).i !== sceneAt(w.s).i;
    if (cur.length && (cur.length >= 3 || chars > 15 || /[.,!?]$/.test(prev.w.trim()) || w.s - prev.e > 0.3 || crossed)) {
      out.push(cur);
      cur = [];
    }
    cur.push(w);
  });
  if (cur.length) out.push(cur);
  return out.map((c, k) => {
    const s = c[0].s;
    const next = out[k + 1]?.[0].s ?? DURATION;
    const e = Math.min(next, sceneAt(s).to - 0.005, c[c.length - 1].e + 0.6);
    const text = c
      .map((x) => x.w.trim().replace(/[.,!?]/g, ''))
      .map((x) => (keep(x) ? x : x.toLowerCase()))
      .join(' ');
    return {text, s, e};
  });
})();

// One video element for the whole reel; only its box changes with the layout, so frames never re-seek.
const Face: React.FC<{t: number}> = ({t}) => {
  const sc = sceneAt(t);
  const clip = clipAt(t);
  let box: React.CSSProperties = {left: 0, top: 0, width: 1080, height: 1920};
  let inner: React.CSSProperties = {left: 0, top: 0, width: 1080, height: 1920};
  if (sc.layout === 'split') {
    const s = SPLIT_SCALE;
    const tx = Math.min(0, Math.max(1080 - 1080 * s, 540 - clip.cx * 1080 * s));
    const ty = Math.max(960 - 1920 * s, 20 - clip.hair * 1920 * s);
    box = {left: 0, top: 960, width: 1080, height: 960};
    inner = {left: tx, top: ty, width: 1080 * s, height: 1920 * s};
  }
  return (
    <div style={{position: 'absolute', overflow: 'hidden', opacity: sc.layout === 'full' ? 0 : 1, ...box}}>
      <div style={{position: 'absolute', ...inner}}>
        <OffthreadVideo src={staticFile('cut.mp4')} style={{width: '100%', height: '100%'}} />
      </div>
    </div>
  );
};

const Captions: React.FC<{t: number}> = ({t}) => {
  const c = CHUNKS.find((x) => t >= x.s && t < x.e);
  if (!c) return null;
  const sc = sceneAt(c.s);
  const y = sc.layout === 'split' ? 0.473 : sc.layout === 'full' ? sc.captionY ?? 0.64 : Math.min(0.8, clipAt(c.s).chin + 0.04);
  const k = Math.min(1, pop(t, c.s, 400));
  return (
    <div
      style={{
        position: 'absolute',
        top: y * 1920,
        left: 0,
        right: 0,
        textAlign: 'center',
        transform: `translateY(-50%) scale(${0.92 + 0.08 * k})`,
        fontFamily: FONT,
        fontWeight: 800,
        fontSize: 78,
        letterSpacing: '-0.04em',
        color: '#fff',
        WebkitTextStroke: '9px #1F1C1A',
        paintOrder: 'stroke fill',
        textShadow: '0 4px 14px rgba(0,0,0,0.35)',
        whiteSpace: 'nowrap',
      }}
    >
      {c.text}
    </div>
  );
};

export const Reel: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const Graphic = sceneAt(t).Graphic;
  return (
    <AbsoluteFill style={{background: '#000'}}>
      <Paper />
      <Face t={t} />
      {Graphic && <Graphic t={t} />}
      <Captions t={t} />
      {SFX.map(([f, s, v], i) => (
        <Sequence key={i} from={Math.round(s * FPS)} durationInFrames={45} layout="none">
          <Audio src={staticFile(`sfx/${f}.wav`)} volume={v} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

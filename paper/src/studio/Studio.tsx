// The studio look, generic part: his face (graded, vignetted, word-by-word captions on his chest) or a
// full-screen graphics set from beats.tsx, hard cuts between the two, zoom-blur dissolves between sets,
// his voice and the sound effects. A new reel only needs a new beats.tsx.
import React from 'react';
import {AbsoluteFill, Audio, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {CTA, SCENES, SFX} from './beats';
import {DURATION, FPS, WORDS, clipAt} from './data';
import type {Clip, Scene} from './data';
import {CommentPill, Lens} from './kit';
import {C, SANS, clamp, ease, mix, pop} from './style';

const VIDEO = staticFile('studio/cut.mp4');
const XF = 0.2;   // half a zoom-blur dissolve between two sets, in seconds

const sceneIndex = (t: number) => {
  let i = 0;
  while (i + 1 < SCENES.length && t >= SCENES[i + 1].from - 1e-3) i++;
  return i;
};

// ---------- his face ----------

// Captions sit on his chest, just under the chin, like the reference. A take framed too low gets lifted
// (at most 13%, the gap below filled with a dark blurred mirror); one still too low gets them above his head.
const framing = (c: Clip) => {
  const lift = clamp(c.chin - 0.63, 0, 0.13);
  const above = c.chin - lift + 0.035 + 0.1 > 0.8;
  return above ? {lift: 0, above, y: c.hair - 0.03} : {lift, above, y: c.chin - lift + 0.035};
};

// Bright and clean (his note 10-25: the first cut's talking parts were "too dark").
const GRADE = 'brightness(1.08) contrast(1.04) saturate(0.93) sepia(0.04)';

// Subtle zooms while he talks (his note 10-25): each phrase (a sentence, or up to a comma, a pause or about
// 2.6 s) glides between 100% and 106%, in then out then in, smootherstep, centred on his face.
const ZOOM = 0.06;
const PHRASES: {s: number; e: number; z0: number; z1: number}[] = (() => {
  const out: {s: number; e: number; z0: number; z1: number}[] = [];
  SCENES.forEach((sc) => {
    if (!sc.face) return;
    const ws = WORDS.filter((w) => w.s >= sc.from - 1e-3 && w.s < sc.to);
    let start = sc.from;
    let k = 0;
    ws.forEach((w, i) => {
      const next = ws[i + 1];
      const end = !next || /[.!?,]$/.test(w.w.trim()) || next.s - w.e > 0.35 || next.s - start > 2.6;
      if (!end) return;
      const e = next ? next.s : sc.to;
      if (e - start < 0.8 && next) return;   // too short to read as a move: fold it into the next phrase
      out.push({s: start, e, z0: k % 2 ? 1 + ZOOM : 1, z1: k % 2 ? 1 : 1 + ZOOM});
      start = e;
      k++;
    });
  });
  return out;
})();
const zoomAt = (t: number) => {
  const p = PHRASES.find((x) => t >= x.s - 1e-3 && t < x.e);
  if (!p) return 1;
  const u = clamp((t - p.s) / (p.e - p.s));
  return mix(p.z0, p.z1, u * u * u * (u * (u * 6 - 15) + 10));
};

const Face: React.FC<{t: number}> = ({t}) => {
  const c = clipAt(t);
  const f = framing(c);
  const origin = `${c.cx * 100}% ${((c.hair + c.chin) / 2) * 100}%`;
  return (
    <AbsoluteFill style={{background: '#0E0D0F', overflow: 'hidden'}}>
      <AbsoluteFill style={{transform: `translateY(${-1920 * f.lift}px) scale(${zoomAt(t)}) translateY(${1920 * f.lift}px)`, transformOrigin: origin}}>
      {f.lift > 0 && (
        <div style={{position: 'absolute', left: -60, top: 1920 * (1 - f.lift) - 130, width: 1200, height: 1920, transform: 'scaleY(-1)', filter: 'blur(30px) brightness(0.9)'}}>
          <OffthreadVideo src={VIDEO} muted style={{width: '100%', height: '100%', objectFit: 'cover', filter: GRADE}} />
        </div>
      )}
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: -1920 * f.lift,
          width: 1080,
          height: 1920,
          // a lifted take fades into the blurred mirror below it instead of ending on a hard edge
          WebkitMaskImage: f.lift > 0 ? 'linear-gradient(180deg, black calc(100% - 110px), transparent 100%)' : undefined,
        }}
      >
        <OffthreadVideo src={VIDEO} muted style={{width: '100%', height: '100%', filter: GRADE}} />
      </div>
      </AbsoluteFill>
      <AbsoluteFill
        style={{
          background:
            'radial-gradient(ellipse 85% 65% at 50% 42%, rgba(10,8,12,0) 55%, rgba(10,8,12,0.16) 82%, rgba(10,8,12,0.3) 100%), linear-gradient(180deg, rgba(10,8,12,0.1) 0%, rgba(10,8,12,0) 14%, rgba(10,8,12,0) 72%, rgba(10,8,12,0.26) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

// ---------- captions ----------

// Two short lines (at most 5 words, 26 characters), broken at punctuation, pauses and scene changes, only
// in face scenes, never ending on a little word ("in", "the"). Casing as he said it; commas and stops off.
type Chunk = {words: {text: string; s: number}[]; s: number; e: number; cta?: boolean};
const WEAK = /^(in|the|a|an|of|to|and|with|on|for|at|my|is|it|or|i)$/i;
const CHUNKS: Chunk[] = (() => {
  const isFace = (t: number) => !!SCENES[sceneIndex(t)].face;
  const inCta = (t: number) => CTA && t >= CTA.from - 1e-3 && t < CTA.to - 1e-3;
  const bare = (w: string) => w.trim().replace(/[.,!]/g, '');
  const out: Chunk[] = [];
  let cur: typeof WORDS = [];
  const flush = (carry = false) => {
    const moved = carry && cur.length > 2 && WEAK.test(bare(cur[cur.length - 1].w)) ? [cur.pop()!] : [];
    if (cur.length) out.push({words: cur.map((w) => ({text: bare(w.w), s: w.s})), s: cur[0].s, e: cur[cur.length - 1].e});
    cur = moved;
  };
  WORDS.forEach((w, k) => {
    if (!isFace(w.s)) return flush();
    if (inCta(w.s)) {
      flush();
      if (!out.length || !out[out.length - 1].cta) out.push({words: [{text: bare(w.w), s: w.s}], s: w.s, e: CTA.to, cta: true});
      return;
    }
    const prev = WORDS[k - 1];
    const chars = cur.map((x) => x.w.trim()).join(' ').length + 1 + w.w.trim().length;
    if (cur.length && (/[.!?,]$/.test(prev.w.trim()) || w.s - prev.e > 0.35 || sceneIndex(prev.s) !== sceneIndex(w.s))) flush();
    else if (cur.length && (cur.length >= 5 || chars > 26)) flush(true);
    cur.push(w);
  });
  flush();
  return out.map((c, k) => {
    const next = out[k + 1]?.s ?? DURATION;
    const sc = SCENES[sceneIndex(c.s)];
    return {...c, e: Math.min(next, sc.to - 0.005, c.cta ? c.e : c.e + 0.55)};
  });
})();

const WORD_IN = 0.14;

const Captions: React.FC<{t: number}> = ({t}) => {
  const c = CHUNKS.find((x) => t >= x.s && t < x.e);
  if (!c) return null;
  const f = framing(clipAt(c.s));
  return (
    <div
      style={{
        position: 'absolute',
        top: f.y * 1920,
        left: 170,
        right: 170,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        transform: f.above ? 'translateY(-100%)' : undefined,
      }}
    >
      <div
        style={{
          width: '100%',
          fontFamily: SANS,
          fontWeight: 500,
          fontSize: 78,
          lineHeight: 1.06,
          letterSpacing: '-0.04em',
          color: '#fff',
          textShadow: '0 2px 4px rgba(0,0,0,0.35), 0 4px 22px rgba(0,0,0,0.38)',
          textAlign: 'center',
          textWrap: 'balance',
        } as React.CSSProperties}
      >
        {c.words.map((w, i) => {
          const k = ease(t, w.s, w.s + WORD_IN);
          return (
            <React.Fragment key={i}>
              {i > 0 && ' '}
              <span
                style={{
                  display: 'inline-block',
                  opacity: k,
                  transform: `translate(${(1 - k) * 10}px, ${(1 - k) * -22}px) scale(${mix(0.8, 1, k)})`,
                  filter: k < 1 ? `blur(${((1 - k) * 6).toFixed(2)}px)` : undefined,
                }}
              >
                {w.text}
              </span>
            </React.Fragment>
          );
        })}
      </div>
      {c.cta && (
        <div style={{marginTop: 18}}>
          <CommentPill word={CTA.word} k={pop(t, CTA.pill, 260)} />
        </div>
      )}
    </div>
  );
};

// ---------- graphics sets ----------

const SetLayer: React.FC<{sc: Scene; t: number; style?: React.CSSProperties}> = ({sc, t, style}) => {
  const S = sc.Set!;
  return (
    <AbsoluteFill style={style}>
      <S t={t} />
    </AbsoluteFill>
  );
};

// Into the next set: the old one pushes in and blurs away, the new one comes out of the blur.
const out = (k: number): React.CSSProperties => ({transform: `scale(${1 + 0.32 * k})`, filter: `blur(${(16 * k).toFixed(2)}px)`});
const inn = (k: number): React.CSSProperties => ({opacity: k, transform: `scale(${0.82 + 0.18 * k})`, filter: k < 1 ? `blur(${(16 * (1 - k)).toFixed(2)}px)` : undefined});

const Graphics: React.FC<{t: number}> = ({t}) => {
  const i = sceneIndex(t);
  const sc = SCENES[i];
  const prev = SCENES[i - 1];
  const next = SCENES[i + 1];
  let layers: React.ReactNode;
  if (prev?.Set && t < sc.from + XF) {
    const k = ease(t, sc.from - XF, sc.from + XF);
    layers = [<SetLayer key="a" sc={prev} t={t} style={out(k)} />, <SetLayer key="b" sc={sc} t={t} style={inn(k)} />];
  } else if (next?.Set && t > next.from - XF) {
    const k = ease(t, next.from - XF, next.from + XF);
    layers = [<SetLayer key="a" sc={sc} t={t} style={out(k)} />, <SetLayer key="b" sc={next} t={t} style={inn(k)} />];
  } else {
    layers = <SetLayer sc={sc} t={t} />;
  }
  return (
    <AbsoluteFill style={{background: C.plane}}>
      {layers}
      <Lens />
    </AbsoluteFill>
  );
};

export const Studio: React.FC = () => {
  const t = useCurrentFrame() / FPS;
  const sc = SCENES[sceneIndex(t)];
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {sc.face ? <Face t={t} /> : <Graphics t={t} />}
      <Captions t={t} />
      <Audio src={VIDEO} />
      {SFX.map(([f, s, v], i) => (
        <Sequence key={i} from={Math.round(s * FPS)} durationInFrames={60} layout="none">
          <Audio src={staticFile(`studio/sfx/${f}.wav`)} volume={v} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};

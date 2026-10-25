// THIS REEL: "claude edits" (10-22 takes, the first paper reel, 10-25). Rewrite this file for every new reel;
// keep finished ones in paper/examples/. One component per beat; times come from the words (`at`), so each
// graphic lands on its word. SCENES, SFX and NAMES at the bottom drive the generic Reel.tsx.
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, interpolate, staticFile} from 'remotion';
import {Card, Check, ClaudeIcon, DottedPath, Folder, Label, Paper, StepHeader, Starburst} from './art';
import {C, FONT, ease, mix, pop} from './style';
import {FPS, at} from './data';
import type {Scene, Sfx} from './data';

type P = {t: number};
const abs = (x: number, y: number, extra?: React.CSSProperties): React.CSSProperties => ({
  position: 'absolute',
  left: x,
  top: y,
  transform: 'translate(-50%, -50%)',
  ...extra,
});
const popStyle = (k: number, from = 0.6): React.CSSProperties => ({opacity: Math.min(1, k * 1.6), scale: `${mix(from, 1, k)}`});

// 0 to 5.3 s: his hook. White title on top the whole time, a row of reels Claude edited pops in under it.
export const Hook: React.FC<P> = ({t}) => {
  const cards = [0, at('edited'), at('video')];
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          top: 268,
          left: 40,
          right: 40,
          textAlign: 'center',
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 74,
          lineHeight: 1.2,
          letterSpacing: '-0.025em',
          color: '#fff',
          textShadow: '0 2px 4px rgba(0,0,0,0.35), 0 6px 24px rgba(0,0,0,0.35)',
        }}
      >
        How I get Claude to
        <br />
        edit my reels for me
      </div>
      {t < 2.5 &&
        cards.map((t0, i) => {
          const k = pop(t, t0, 240);
          if (k <= 0) return null;
          return (
            <div
              key={i}
              style={{
                ...abs(540 + (i - 1) * 290, 745),
                width: 266,
                height: 473,
                borderRadius: 16,
                overflow: 'hidden',
                boxShadow: '0 10px 30px rgba(0,0,0,0.35)',
                ...popStyle(k, 0.8),
              }}
            >
              <Sequence from={Math.round(t0 * FPS)} layout="none">
                <OffthreadVideo src={staticFile(`assets/reel${i + 1}.mp4`)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
              </Sequence>
            </div>
          );
        })}
    </AbsoluteFill>
  );
};

// 5.3 s, full paper: his raw clips drop into the Raw footage folder, a dotted line carries one to Claude.
export const RawFootage: React.FC<P> = ({t}) => {
  const t0 = 5.3;
  const send = at('send');
  const raw = at('raw');
  const solid = ease(t, t0 + 0.08, t0 + 0.28);
  const line = ease(t, send, send + 0.32);
  const icon = pop(t, send + 0.16);
  const fly = ease(t, raw, raw + 0.42);
  const bump = 1 + 0.1 * Math.sin(Math.min(1, Math.max(0, (t - raw - 0.42) / 0.25)) * Math.PI);
  return (
    <AbsoluteFill>
      <Paper />
      <div style={abs(310, 770)}>
        <Folder w={400} solid={solid} open={0.55}>
          {[0, 1, 2].map((i) => {
            const k = ease(t, t0 + 0.2 + i * 0.09, t0 + 0.48 + i * 0.09);
            return (
              <Img
                key={i}
                src={staticFile(`assets/raw${i + 1}.jpg`)}
                style={{
                  position: 'absolute',
                  left: 60 + i * 96,
                  top: mix(-360, -30 + (i === 1 ? -16 : 0), k),
                  width: 112,
                  height: 170,
                  objectFit: 'cover',
                  border: '4px solid #fff',
                  borderRadius: 6,
                  rotate: `${(i - 1) * 6}deg`,
                  boxShadow: '0 4px 10px rgba(0,0,0,0.2)',
                  opacity: k > 0 ? 1 : 0,
                }}
              />
            );
          })}
        </Folder>
      </div>
      <Label text="Raw footage" color={C.terracotta} size={50} style={abs(310, 1010, {opacity: solid})} />
      <DottedPath d="M 530 770 L 670 770" p={line} w={1080} h={1920} />
      <div style={abs(800, 770, popStyle(icon))}>
        <div style={{scale: `${bump}`}}>
          <ClaudeIcon size={230} />
        </div>
      </div>
      <Label text="Claude" size={50} style={abs(800, 1010, {opacity: icon})} />
      {fly > 0 && fly < 1 && (
        <Img
          src={staticFile('assets/raw2.jpg')}
          style={abs(mix(380, 790, fly), 770 - Math.sin(fly * Math.PI) * 90, {
            width: mix(92, 50, fly),
            height: mix(140, 76, fly),
            objectFit: 'cover',
            border: '4px solid #fff',
            borderRadius: 6,
            boxShadow: '0 6px 14px rgba(0,0,0,0.25)',
          })}
        />
      )}
    </AbsoluteFill>
  );
};

// 7.1 s, split: all you need is Claude Code installed.
export const Install: React.FC<P> = ({t}) => {
  const claude = at('claude', 8);
  const inst = at('installed');
  const ghost = ease(t, 7.1333, 7.3);
  const icon = pop(t, claude);
  const bar = ease(t, inst, inst + 0.5);
  const done = pop(t, inst + 0.55);
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <div style={abs(540, 340, {width: 250, height: 250, borderRadius: 60, border: `5px dashed rgba(75,66,58,${0.35 * ghost * (1 - icon)})`})} />
      <div style={abs(540, 340, popStyle(icon))}>
        <ClaudeIcon size={250} />
      </div>
      <Label text="Claude Code" size={54} style={abs(540, 540, {opacity: Math.min(1, icon * 1.5)})} />
      {t >= inst && done < 0.05 && (
        <div style={abs(540, 625, {width: 380, height: 20, borderRadius: 10, background: 'rgba(75,66,58,0.14)', overflow: 'hidden'})}>
          <div style={{width: `${bar * 100}%`, height: '100%', background: C.terracotta, borderRadius: 10}} />
        </div>
      )}
      {done > 0 && (
        <div
          style={abs(540, 630, {
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '12px 30px 12px 14px',
            borderRadius: 50,
            background: C.terracotta,
            color: '#fff',
            fontFamily: FONT,
            fontWeight: 800,
            fontSize: 36,
            letterSpacing: '-0.03em',
            ...popStyle(done, 0.7),
          })}
        >
          <Check size={44} color="rgba(255,255,255,0.25)" />
          Installed
        </div>
      )}
    </AbsoluteFill>
  );
};

// 10 s, split: Claude at the top, a tree to three rule folders (his folder-tree scene).
export const ThreeRules: React.FC<P> = ({t}) => {
  const t0 = 9.9667;
  const move = ease(t, t0, t0 + 0.32);
  const tree = ease(t, at('taught'), at('taught') + 0.3);
  const three = at('three', 10);
  const xs = [250, 540, 830];
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <div style={abs(540, mix(340, 175, move))}>
        <ClaudeIcon size={mix(250, 140, move)} />
      </div>
      <svg width={1080} height={960} style={{position: 'absolute', left: 0, top: 0}}>
        <path
          d="M 540 255 V 350 M 250 350 H 830 M 250 350 V 425 M 540 350 V 425 M 830 350 V 425"
          stroke={C.line}
          strokeWidth={3}
          fill="none"
          pathLength={1}
          strokeDasharray="1 1"
          strokeDashoffset={1 - tree}
        />
      </svg>
      {xs.map((x, i) => {
        const k = pop(t, three + i * 0.1);
        const solid = ease(t, three + i * 0.1 + 0.1, three + i * 0.1 + 0.3);
        return (
          <React.Fragment key={i}>
            <div style={abs(x, 545, popStyle(k, 0.7))}>
              <Folder w={210} solid={solid} />
            </div>
            <Label text={`Rule ${i + 1}`} color={C.terracotta} size={46} style={abs(x, 695, {opacity: Math.min(1, k * 1.5)})} />
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// 13.1 s, split: Step 1. A timeline whose pauses get found by the playhead, then cut out.
export const DeadSpace: React.FC<P> = ({t}) => {
  const t0 = 13.1;
  const kill = at('kill');
  const dead = at('dead');
  const widths = [150, 118, 176, 104, 142];
  const gap = 62;
  const collapse = ease(t, dead, dead + 0.4);
  const g = gap * (1 - collapse);
  const total = widths.reduce((a, b) => a + b, 0) + g * 4;
  let x = 540 - total / 2;
  const head = interpolate(t, [kill, dead - 0.05], [70, 1010], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const secs = interpolate(t, [at('every', 14), dead + 0.4], [3.4, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const counter = pop(t, at('every', 14) - 0.2);
  const items: React.ReactNode[] = [];
  widths.forEach((w, i) => {
    const k = pop(t, t0 + 0.15 + i * 0.06, 260);
    items.push(
      <div
        key={`c${i}`}
        style={{
          position: 'absolute',
          left: x,
          top: 380,
          width: w,
          height: 130,
          borderRadius: 16,
          background: `linear-gradient(180deg, #8DD6F6, ${C.folder})`,
          boxShadow: '0 6px 14px rgba(40,90,120,0.22)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 6,
          ...popStyle(k, 0.5),
        }}
      >
        {Array.from({length: Math.floor(w / 18)}).map((_, j) => (
          <div key={j} style={{width: 6, borderRadius: 3, background: 'rgba(255,255,255,0.9)', height: 18 + Math.abs(Math.sin((i + 1) * 7 + j * 1.9)) * 56}} />
        ))}
      </div>,
    );
    x += w;
    if (i < widths.length - 1) {
      const hit = t >= kill && head > x + g / 2;
      items.push(
        <div
          key={`g${i}`}
          style={{
            position: 'absolute',
            left: x + 6,
            top: 400,
            width: Math.max(0, g - 12),
            height: 90,
            borderRadius: 10,
            background: hit
              ? 'repeating-linear-gradient(45deg, rgba(203,96,62,0.55) 0 7px, rgba(203,96,62,0.12) 7px 15px)'
              : 'repeating-linear-gradient(45deg, rgba(75,66,58,0.28) 0 7px, rgba(75,66,58,0.06) 7px 15px)',
            opacity: pop(t, t0 + 0.4) * (1 - collapse * 0.7),
          }}
        />,
      );
      x += g;
    }
  });
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={1} title="Kill dead space" y={110} k={ease(t, t0, t0 + 0.18)} />
      {items}
      {t >= kill && t < dead + 0.05 && (
        <div style={{position: 'absolute', left: head - 3, top: 345, width: 6, height: 200, background: C.terracotta, borderRadius: 3}}>
          <div style={{position: 'absolute', left: -11, top: -14, width: 28, height: 28, background: C.terracotta, rotate: '45deg', borderRadius: 4}} />
        </div>
      )}
      <div style={abs(540, 680, {textAlign: 'center', ...popStyle(counter, 0.8)})}>
        <Label text="dead space" color={C.inkSoft} size={40} />
        <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 112, letterSpacing: '-0.05em', color: C.terracotta, lineHeight: 1}}>
          {secs.toFixed(1)}s
        </div>
      </div>
    </AbsoluteFill>
  );
};

// 16.3 s, split: Step 2. Fancy caption styles get struck out, then an arrow points at his real caption.
export const PlainCaptions: React.FC<P> = ({t}) => {
  const t0 = 16.2667;
  const cap = at('caption');
  const plain = at('plain');
  const these = at('these');
  const white = at('white');
  const out = ease(t, these, these + 0.22);
  const samples: {node: React.ReactNode; y: number; rot: number}[] = [
    {
      y: 300,
      rot: -3,
      node: (
        <div style={{display: 'flex', gap: 10}}>
          {['SO', 'GOOD'].map((w) => (
            <span key={w} style={{background: '#FFE04A', color: '#111', padding: '2px 14px', borderRadius: 8, fontFamily: FONT, fontWeight: 900, fontSize: 66}}>
              {w}
            </span>
          ))}
        </div>
      ),
    },
    {
      y: 445,
      rot: 0,
      node: (
        <span
          style={{
            fontFamily: 'Georgia, serif',
            fontStyle: 'italic',
            fontWeight: 700,
            fontSize: 84,
            background: 'linear-gradient(90deg, #FF4FA3, #FF9F2E, #8B5CF6)',
            WebkitBackgroundClip: 'text',
            color: 'transparent',
          }}
        >
          captions
        </span>
      ),
    },
    {
      y: 590,
      rot: 4,
      node: (
        <span style={{fontFamily: FONT, fontWeight: 900, fontSize: 70, color: '#39D26B', WebkitTextStroke: '12px #111', paintOrder: 'stroke fill'}}>WOW!!</span>
      ),
    },
  ];
  const label = pop(t, these + 0.05);
  const arrow = ease(t, these + 0.15, these + 0.45);
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={2} title="Plain white captions" y={110} k={ease(t, t0, t0 + 0.18)} />
      {samples.map((s, i) => {
        const k = pop(t, cap + i * 0.12);
        const strike = ease(t, plain + i * 0.07, plain + 0.25 + i * 0.07);
        if (k <= 0 || out >= 1) return null;
        return (
          <div key={i} style={abs(540, s.y, {...popStyle(k, 0.6), opacity: Math.min(1, k * 1.6) * mix(1, 0.45, strike) * (1 - out), rotate: `${s.rot}deg`})}>
            <div style={{position: 'relative', translate: `${-out * 160}px 0`}}>
              {s.node}
              <div
                style={{
                  position: 'absolute',
                  left: -20,
                  top: '50%',
                  height: 9,
                  width: `calc(${strike * 100}% + ${strike * 40}px)`,
                  background: C.terracotta,
                  borderRadius: 5,
                  rotate: '-4deg',
                }}
              />
            </div>
          </div>
        );
      })}
      {label > 0 && (
        <div style={abs(540, 470, {display: 'flex', alignItems: 'center', gap: 18, ...popStyle(label, 0.7)})}>
          <Label text="These ones" size={58} />
          <Check size={58} k={pop(t, white)} />
        </div>
      )}
      <DottedPath
        d="M 540 545 C 540 640, 540 700, 540 800"
        p={arrow}
        w={1080}
        h={960}
        dot={7}
        arrow={{x: 540, y: 800, angle: 90}}
      />
    </AbsoluteFill>
  );
};

// 20.2 s, face: the overlay sits right above his head, a checklist of the three rules.
export const OverlayCard: React.FC<P> = ({t}) => {
  const k = pop(t, at('overlays'), 220);
  const hi = ease(t, at('like', 21), at('like', 21) + 0.2);
  const tick = pop(t, at('head'));
  if (k <= 0) return null;
  const rows = ['Kill dead space', 'Plain white captions', 'Overlays above my head'];
  return (
    <div style={abs(540, 445, {width: 840, ...popStyle(k, 0.75)})}>
      <Card>
        <div style={{display: 'flex', alignItems: 'center', gap: 16, padding: '24px 30px', borderBottom: `1.5px solid ${C.cardLine}`}}>
          <Starburst size={44} color={C.terracotta} />
          <div style={{fontWeight: 800, fontSize: 40, letterSpacing: '-0.03em', color: C.ink}}>Claude's edit rules</div>
        </div>
        {rows.map((r, i) => (
          <div
            key={r}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 22,
              padding: '20px 30px',
              borderTop: i ? `1.5px solid ${C.cardLine}` : undefined,
              background: i === 2 ? `rgba(203,96,62,${0.1 * hi})` : undefined,
            }}
          >
            <div style={{fontWeight: 900, fontSize: 40, color: C.terracotta, width: 30}}>{i + 1}</div>
            <div style={{flex: 1, fontWeight: 700, fontSize: 40, letterSpacing: '-0.03em', color: C.ink}}>{r}</div>
            <Check size={46} k={i < 2 ? 1 : tick} />
          </div>
        ))}
      </Card>
    </div>
  );
};

// 22.8 s, split: a ring fills around Claude's mark while the minutes count up to 15.
export const Minutes: React.FC<P> = ({t}) => {
  const t0 = 22.8333;
  const k = pop(t, t0 + 0.05);
  const fill = ease(t, at('took'), at('minutes') + 0.1);
  const n = Math.round(interpolate(t, [at('claude', 24), at('15') + 0.25], [0, 15], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
  const num = pop(t, at('claude', 24));
  const r = 160;
  const L = 2 * Math.PI * r;
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <div style={abs(540, 370, popStyle(k, 0.7))}>
        <div style={{position: 'relative', width: 400, height: 400}}>
          <div style={{position: 'absolute', inset: 34, borderRadius: '50%', background: 'rgba(255,255,255,0.35)', boxShadow: 'inset 0 0 0 2px rgba(203,96,62,0.15)'}} />
          <svg width={400} height={400} style={{position: 'absolute', inset: 0, rotate: '-90deg'}}>
            <circle cx={200} cy={200} r={r} stroke="rgba(75,66,58,0.12)" strokeWidth={22} fill="none" />
            <circle cx={200} cy={200} r={r} stroke={C.terracotta} strokeWidth={22} fill="none" strokeLinecap="round" strokeDasharray={L} strokeDashoffset={L * (1 - fill)} />
          </svg>
          <div style={abs(200, 200)}>
            <Starburst size={170} color={C.terracotta} spin={(t - t0) * 45} />
          </div>
        </div>
      </div>
      <div style={abs(540, 690, {display: 'flex', alignItems: 'baseline', gap: 18, ...popStyle(num, 0.7)})}>
        <span style={{fontFamily: FONT, fontWeight: 900, fontSize: 130, letterSpacing: '-0.05em', color: C.terracotta}}>{n}</span>
        <span style={{fontFamily: FONT, fontWeight: 800, fontSize: 76, letterSpacing: '-0.04em', color: C.ink}}>minutes</span>
      </div>
    </AbsoluteFill>
  );
};

// 27.9 s, full paper: his recap. The editor folder in the middle, the steps pointing in, then FREE.
export const Recap: React.FC<P> = ({t}) => {
  const t0 = 27.8667;
  const solid = ease(t, t0 + 0.05, t0 + 0.25);
  const stamp = pop(t, at('free'), 260);
  const corners = [
    {x: 260, y: 400, n: 'Step 1.', s: 'Kill dead space', d: 'M 280 470 C 300 560, 340 620, 405 668', a: {x: 405, y: 668, angle: 40}},
    {x: 820, y: 400, n: 'Step 2.', s: 'White captions', d: 'M 800 470 C 780 560, 740 620, 675 668', a: {x: 675, y: 668, angle: 140}},
    {x: 260, y: 1150, n: 'Step 3.', s: 'Overlays', d: 'M 280 1085 C 300 1010, 330 960, 385 930', a: {x: 385, y: 930, angle: -35}},
    {x: 820, y: 1150, n: 'Done in', s: '15 minutes', d: 'M 800 1085 C 780 1010, 750 960, 695 930', a: {x: 695, y: 930, angle: -145}},
  ];
  return (
    <AbsoluteFill>
      <Paper />
      <div style={abs(540, 800)}>
        <Folder w={340} solid={solid} />
      </div>
      <Label text="My Claude editor" size={50} style={abs(540, 990, {opacity: solid})} />
      {corners.map((c, i) => {
        const t1 = t0 + 0.12 + i * 0.22;
        const k = pop(t, t1);
        return (
          <React.Fragment key={i}>
            <div style={abs(c.x, c.y, {textAlign: 'center', ...popStyle(k, 0.7)})}>
              <Label text={c.n} color={C.terracotta} size={50} />
              <Label text={c.s} size={54} />
            </div>
            <DottedPath d={c.d} p={ease(t, t1 + 0.08, t1 + 0.4)} w={1080} h={1920} dot={6} arrow={c.a} />
          </React.Fragment>
        );
      })}
      {stamp > 0 && (
        <div
          style={abs(540, 790, {
            padding: '10px 44px',
            borderRadius: 22,
            background: C.terracotta,
            color: '#fff',
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: 110,
            letterSpacing: '-0.03em',
            border: '6px solid #fff',
            boxShadow: '0 14px 30px rgba(120,50,20,0.35)',
            rotate: '-8deg',
            opacity: Math.min(1, stamp * 2),
            scale: `${mix(2.2, 1, stamp)}`,
          })}
        >
          FREE
        </div>
      )}
    </AbsoluteFill>
  );
};

// 31.5 s, face: his CTA. A white search pill types the comment word, the arrow button turns dark.
export const Cta: React.FC<P> = ({t}) => {
  const word = 'EDIT';
  const t0 = at('edit', 31);
  const k = pop(t, 31.6, 220);
  const typed = Math.max(0, Math.min(word.length, Math.floor((t - t0) / 0.07) + 1));
  const done = t >= t0 + word.length * 0.07 + 0.08;
  const caret = !done && Math.floor(t * 4) % 2 === 0;
  if (k <= 0) return null;
  return (
    <div
      style={abs(540, 380, {
        width: 830,
        height: 116,
        borderRadius: 58,
        background: '#fff',
        boxShadow: '0 12px 34px rgba(0,0,0,0.28)',
        display: 'flex',
        alignItems: 'center',
        padding: '0 22px 0 34px',
        gap: 20,
        ...popStyle(k, 0.8),
      })}
    >
      <Starburst size={54} color={C.terracotta} />
      <div style={{flex: 1, fontFamily: FONT, fontWeight: 800, fontSize: 52, letterSpacing: '-0.02em', color: C.ink}}>
        {t >= t0 ? word.slice(0, typed) : ''}
        <span style={{opacity: caret ? 1 : 0, color: C.terracotta}}>|</span>
      </div>
      <div
        style={{
          width: 76,
          height: 76,
          borderRadius: 40,
          background: done ? C.ink : '#D9D5CE',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          scale: done ? `${mix(1.15, 1, ease(t, t0 + 0.36, t0 + 0.55))}` : '1',
        }}
      >
        <svg width={38} height={38} viewBox="0 0 24 24">
          <path d="M5 12 H18 M12.5 6 L18.5 12 L12.5 18" stroke={done ? C.terracotta : '#fff'} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" fill="none" />
        </svg>
      </div>
    </div>
  );
};

// Names that keep their capital in the lowercase captions.
export const NAMES = ['Claude', 'Code'];

// His three layouts with hard cuts, one per sentence or so, each starting where a take starts.
export const SCENES: Scene[] = [
  {from: 0, to: 5.3, layout: 'face', Graphic: Hook},
  {from: 5.3, to: 7.1333, layout: 'full', captionY: 0.64, Graphic: RawFootage},
  {from: 7.1333, to: 9.9667, layout: 'split', Graphic: Install},
  {from: 9.9667, to: 13.1, layout: 'split', Graphic: ThreeRules},
  {from: 13.1, to: 16.2667, layout: 'split', Graphic: DeadSpace},
  {from: 16.2667, to: 20.2, layout: 'split', Graphic: PlainCaptions},
  {from: 20.2, to: 22.8333, layout: 'face', Graphic: OverlayCard},
  {from: 22.8333, to: 25.6667, layout: 'split', Graphic: Minutes},
  {from: 25.6667, to: 27.8667, layout: 'face'},
  {from: 27.8667, to: 31.5333, layout: 'full', captionY: 0.7, Graphic: Recap},
  {from: 31.5333, to: 99, layout: 'face', Graphic: Cta},
];

// Soft pops on graphics, a light whoosh into full-paper scenes, key clicks on the typed CTA. No music.
export const SFX: Sfx[] = [
  ['pop_light_3005', 0.02, 0.3],
  ['pop_light_3005', at('edited'), 0.3],
  ['pop_light_3005', at('video'), 0.3],
  ['whoosh_fast_1490', 5.27, 0.3],
  ['pop_light_3005', 5.55, 0.3],
  ['pop_light_3005', at('send') + 0.16, 0.35],
  ['pop_dry_2356', at('raw') + 0.42, 0.35],
  ['whoosh_air_1489', 7.1, 0.18],
  ['pop_light_3005', at('claude', 8), 0.35],
  ['pop_dry_2356', at('installed') + 0.55, 0.4],
  ['pop_light_3005', at('three', 10), 0.3],
  ['pop_light_3005', at('three', 10) + 0.2, 0.3],
  ['pop_light_3005', 13.25, 0.3],
  ['whoosh_fast_1490', at('dead') - 0.05, 0.25],
  ['pop_light_3005', at('caption'), 0.3],
  ['pop_hard_click_2364', at('plain'), 0.25],
  ['pop_dry_2356', at('white'), 0.35],
  ['whoosh_air_1489', 20.17, 0.18],
  ['pop_light_3005', at('overlays'), 0.35],
  ['pop_dry_2356', at('head'), 0.35],
  ['pop_light_3005', 22.88, 0.3],
  ['lab_ding', at('15') + 0.25, 0.22],
  ['whoosh_fast_1490', 27.84, 0.3],
  ['pop_light_3005', 28.0, 0.25],
  ['pop_light_3005', 28.44, 0.25],
  ['pop_dry_2356', at('free'), 0.55],
  ['pop_light_3005', 31.6, 0.3],
  ['pop_hard_click_2364', at('edit', 31), 0.22],
  ['pop_hard_click_2364', at('edit', 31) + 0.07, 0.22],
  ['pop_hard_click_2364', at('edit', 31) + 0.14, 0.22],
  ['pop_hard_click_2364', at('edit', 31) + 0.21, 0.22],
  ['pop_dry_2356', at('edit', 31) + 0.36, 0.3],
];

// THIS REEL: "ai editor h2" (10-25 takes, two spoken hooks x two cover titles = four reels, 10-26). The body is the
// same take in both cuts, so every body time is relative to K(i), the start of body clip i; only the hook
// differs (NAME). COVER picks the title. Rewrite this file for every new reel; keep finished ones in examples/.
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, Sequence, staticFile} from 'remotion';
import {Card, Check, ClaudeIcon, DottedPath, Folder, Label, Paper, StepHeader, Starburst} from './art';
import {C, FONT, ease, mix, pop} from './style';
import {CLIPS, FPS, NAME, at} from './data';
import type {Scene, Sfx} from './data';

const COVER: 1 | 2 = 2;
const TITLE = COVER === 1 ? ['Everything you need to know', 'about editing with AI'] : ['Build your own', 'AI editor for free'];
const H1 = NAME === 'ai editor h1';

// Body clips (same in both cuts): 0 First, 1 Create a folder, 2 inside that folder, 3 Raw footage, 4 references,
// 5 new Claude chat, 6 Give Claude the links, 7 tell it to install, 8 lock in your style, 9 using the same prompt,
// 10 film, 11 place the raw footage, 12 the edit prompt, 13 adjustment, 14 voila, 15 complete reel,
// 16 my workflow, 17 comment.
const B = at('first');
const B0 = CLIPS.findIndex((c) => c.t0 >= B - 0.02);
const K = (i: number) => CLIPS[B0 + i].t0;
const w = (word: string, i: number) => at(word, K(i));

type P = {t: number};
const abs = (x: number, y: number, extra?: React.CSSProperties): React.CSSProperties => ({
  position: 'absolute',
  left: x,
  top: y,
  transform: 'translate(-50%, -50%)',
  ...extra,
});
const popStyle = (k: number, from = 0.6): React.CSSProperties => ({opacity: Math.min(1, k * 1.6), scale: `${mix(from, 1, k)}`});

// A white Claude chat card: greeting, the prompt typing in, model name and the orange send button.
const PromptCard: React.FC<{t: number; t0: number; lines: string[]; width?: number; size?: number; send?: number}> = ({t, t0, lines, width = 860, size = 30, send}) => {
  const typed = ease(t, t0 + 0.1, t0 + 1.1);
  const total = lines.join('').length;
  let left = Math.round(total * typed);
  const sent = send !== undefined && t >= send;
  return (
    <Card style={{width}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '22px 28px 10px'}}>
        <Starburst size={34} color={C.terracotta} />
        <div style={{fontWeight: 800, fontSize: 32, letterSpacing: '-0.03em', color: C.ink}}>How can I help you today?</div>
      </div>
      <div style={{margin: '8px 22px 0', padding: '16px 20px', borderRadius: 16, border: `1.5px solid ${C.cardLine}`, background: '#FBFAF8', minHeight: 100}}>
        {lines.map((l, i) => {
          const shown = l.slice(0, Math.max(0, left));
          left -= l.length;
          return (
            <div key={i} style={{fontWeight: 600, fontSize: size, lineHeight: 1.35, letterSpacing: '-0.02em', color: i === 0 ? C.ink : C.inkSoft, minHeight: size * 1.35}}>
              {shown}
            </div>
          );
        })}
      </div>
      <div style={{display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 16, padding: '14px 26px 20px'}}>
        <div style={{fontWeight: 700, fontSize: 24, color: C.inkSoft}}>Opus 5.5</div>
        <div
          style={{
            width: 52,
            height: 52,
            borderRadius: 14,
            background: C.terracotta,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            scale: sent ? `${mix(1.2, 1, ease(t, send!, send! + 0.2))}` : '1',
            opacity: typed >= 1 ? 1 : 0.45,
          }}
        >
          <svg width={28} height={28} viewBox="0 0 24 24">
            <path d="M12 19 V6 M6 11.5 L12 5.5 L18 11.5" stroke="#fff" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" fill="none" />
          </svg>
        </div>
      </div>
    </Card>
  );
};

// A browser window icon (three dots, address bar, globe).
const Browser: React.FC<{size: number}> = ({size}) => (
  <div style={{width: size, height: size * 0.8, borderRadius: size * 0.1, background: '#fff', border: `3px solid ${C.cardLine}`, boxShadow: '0 10px 24px rgba(40,30,20,0.18)', overflow: 'hidden'}}>
    <div style={{height: size * 0.18, background: '#EFEBE5', display: 'flex', alignItems: 'center', gap: size * 0.035, padding: `0 ${size * 0.06}px`}}>
      {['#E9695E', '#F2BE4F', '#62C554'].map((c) => (
        <div key={c} style={{width: size * 0.055, height: size * 0.055, borderRadius: 99, background: c}} />
      ))}
      <div style={{flex: 1, height: size * 0.08, marginLeft: size * 0.04, borderRadius: 99, background: '#fff'}} />
    </div>
    <div style={{display: 'flex', alignItems: 'center', justifyContent: 'center', height: size * 0.62}}>
      <svg width={size * 0.36} height={size * 0.36} viewBox="0 0 24 24">
        <circle cx={12} cy={12} r={10} stroke="#7FA7C9" strokeWidth={1.8} fill="none" />
        <path d="M2 12 H22 M12 2 C 7 7, 7 17, 12 22 M12 2 C 17 7, 17 17, 12 22" stroke="#7FA7C9" strokeWidth={1.8} fill="none" />
      </svg>
    </div>
  </div>
);

// A phone-shaped reel card playing one of his reels (or a still).
const ReelCard: React.FC<{src: string; t0: number; w: number; style?: React.CSSProperties}> = ({src, t0, w: cw, style}) => (
  <div style={{width: cw, height: cw * 1.78, borderRadius: 14, overflow: 'hidden', border: '4px solid #fff', boxShadow: '0 10px 26px rgba(0,0,0,0.3)', background: '#222', ...style}}>
    {src.endsWith('.mp4') ? (
      <Sequence from={Math.round(t0 * FPS)} layout="none">
        <OffthreadVideo src={staticFile(src)} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
      </Sequence>
    ) : (
      <Img src={staticFile(src)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    )}
  </div>
);

// Hook: the cover title on top the whole time, a row of edited reels under it on the first line.
export const Hook: React.FC<P> = ({t}) => {
  const cards = H1 ? [0, at('editing'), at('videos')] : [0, at('build'), at('editor')];
  const off = ease(t, (H1 ? at('so') : at('step')) - 0.15, (H1 ? at('so') : at('step')) + 0.05);
  return (
    <AbsoluteFill>
      <div
        style={{
          position: 'absolute',
          top: 250,
          left: 30,
          right: 30,
          textAlign: 'center',
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 72,
          lineHeight: 1.2,
          letterSpacing: '-0.025em',
          color: '#fff',
          textShadow: '0 2px 4px rgba(0,0,0,0.35), 0 6px 24px rgba(0,0,0,0.35)',
        }}
      >
        {TITLE[0]}
        <br />
        {TITLE[1]}
      </div>
      {off < 1 &&
        cards.map((t0, i) => {
          const k = pop(t, t0, 240);
          if (k <= 0) return null;
          return (
            <div key={i} style={abs(540 + (i - 1) * 290, 745, {...popStyle(k, 0.8), opacity: Math.min(1, k * 1.6) * (1 - off)})}>
              <ReelCard src={`assets/reel${i + 1}.mp4`} t0={t0} w={258} style={{borderRadius: 16, border: 'none'}} />
            </div>
          );
        })}
    </AbsoluteFill>
  );
};

// Body 0, split: Step 1. The Claude desktop app gets the check, the browser gets struck out.
export const DesktopApp: React.FC<P> = ({t}) => {
  const t0 = K(0);
  const app = pop(t, w('claude', 0));
  const br = pop(t, w('browser', 0));
  const slide = ease(t, w('not', 0), w('not', 0) + 0.3);
  const strike = ease(t, w('version', 0), w('version', 0) + 0.25);
  const tick = pop(t, w('version', 0) + 0.2);
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={1} title="Set it up" y={110} k={ease(t, t0, t0 + 0.18)} />
      <div style={abs(mix(540, 300, slide), 450, popStyle(app))}>
        <ClaudeIcon size={250} />
      </div>
      <Label text="Desktop app" size={50} style={abs(mix(540, 300, slide), 655, {opacity: Math.min(1, app * 1.5)})} />
      <div style={abs(mix(540, 300, slide) + 110, 340, {scale: `${tick}`})}>
        <Check size={70} />
      </div>
      {br > 0 && (
        <>
          <div style={abs(780, 450, {...popStyle(br), opacity: Math.min(1, br * 1.6) * mix(1, 0.5, strike)})}>
            <Browser size={250} />
          </div>
          <Label text="Browser" size={50} style={abs(780, 655, {opacity: Math.min(1, br * 1.5) * mix(1, 0.5, strike)})} />
          <svg width={1080} height={960} style={{position: 'absolute', left: 0, top: 0}}>
            <path d="M 660 340 L 900 570 M 900 340 L 660 570" stroke={C.terracotta} strokeWidth={14} strokeLinecap="round" pathLength={1} strokeDasharray="1 1" strokeDashoffset={1 - strike} fill="none" />
          </svg>
        </>
      )}
    </AbsoluteFill>
  );
};

// Body 1, full paper: a ghost folder fills in on "folder", gets its name on "called".
export const CreateFolder: React.FC<P> = ({t}) => {
  const t0 = K(1);
  const ghost = pop(t, w('folder', 1) - 0.1);
  const solid = ease(t, w('computer', 1), w('computer', 1) + 0.3);
  const name = pop(t, w('called', 1) + 0.15);
  return (
    <AbsoluteFill>
      <Paper />
      <StepHeader n={1} title="Set it up" y={300} k={ease(t, t0, t0 + 0.18)} />
      <div style={abs(540, 800, popStyle(ghost, 0.7))}>
        <Folder w={440} solid={solid} />
      </div>
      <Label text="AI Video Editor" color={C.terracotta} size={62} style={abs(540, 1060, popStyle(name, 0.7))} />
    </AbsoluteFill>
  );
};

// Body 2 to 4, split: the folder moves up, a tree draws to three subfolders, each named on its word.
export const Subfolders: React.FC<P> = ({t}) => {
  const t0 = K(2);
  const move = ease(t, t0, t0 + 0.32);
  const tree = ease(t, w('three', 2) - 0.1, w('three', 2) + 0.25);
  const xs = [230, 540, 850];
  const names = ['Raw footage', 'References', 'Exports'];
  const named = [w('raw', 3), w('references', 3), w('exports', 3)];
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={1} title="Set it up" y={110} k={1} />
      <div style={abs(540, mix(470, 300, move))}>
        <Folder w={mix(300, 190, move)} />
      </div>
      <Label text="AI Video Editor" size={36} style={abs(540, mix(640, 400, move))} />
      <svg width={1080} height={960} style={{position: 'absolute', left: 0, top: 0}}>
        <path
          d="M 540 430 V 490 M 230 490 H 850 M 230 490 V 540 M 540 490 V 540 M 850 490 V 540"
          stroke={C.line}
          strokeWidth={3}
          fill="none"
          pathLength={1}
          strokeDasharray="1 1"
          strokeDashoffset={1 - tree}
        />
      </svg>
      {xs.map((x, i) => {
        const k = pop(t, w('subfolders', 2) + i * 0.1);
        const solid = ease(t, named[i], named[i] + 0.2);
        const lab = pop(t, named[i]);
        return (
          <React.Fragment key={i}>
            <div style={abs(x, 640, popStyle(k, 0.7))}>
              <Folder w={200} solid={solid} open={i === 0 ? 0.5 * solid : 0}>
                {i === 0 &&
                  [0, 1].map((j) => (
                    <Img
                      key={j}
                      src={staticFile(`assets/raw${j + 1}.jpg`)}
                      style={{position: 'absolute', left: 50 + j * 54, top: mix(-140, -20, ease(t, named[0] + 0.1, named[0] + 0.4)), width: 60, height: 90, objectFit: 'cover', border: '3px solid #fff', borderRadius: 4, rotate: `${(j - 0.5) * 10}deg`, opacity: solid}}
                    />
                  ))}
              </Folder>
            </div>
            <Label text={names[i]} color={C.terracotta} size={42} style={abs(x, 780, popStyle(lab, 0.7))} />
          </React.Fragment>
        );
      })}
    </AbsoluteFill>
  );
};

// Body 5, full paper: a new Claude chat, the environment menu opens on "select", Local gets picked, then a
// dotted line points Claude at the AI Video Editor folder.
export const ClaudeChat: React.FC<P> = ({t}) => {
  const t0 = K(5);
  const card = pop(t, t0 + 0.05, 220);
  const menu = ease(t, w('select', 5), w('select', 5) + 0.2);
  const pick = t >= w('local', 5) + 0.15;
  const read = pop(t, w('read', 5));
  const point = w('point', 5);
  const down = ease(t, point - 0.25, point + 0.05);
  const icon = pop(t, point);
  const line = ease(t, point + 0.15, point + 0.5);
  const fold = pop(t, w('folder', 5) - 0.15);
  const rows: [string, string][] = [
    ['Local', 'This computer'],
    ['Cloud', 'Anthropic cloud'],
  ];
  return (
    <AbsoluteFill>
      <Paper />
      <div style={abs(540, mix(700, 560, down), {...popStyle(card, 0.8), opacity: Math.min(1, card * 1.6) * (1 - down * 0.25)})}>
        <Card style={{width: 860}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '24px 30px', borderBottom: `1.5px solid ${C.cardLine}`}}>
            <Starburst size={38} color={C.terracotta} />
            <div style={{fontWeight: 800, fontSize: 36, letterSpacing: '-0.03em', color: C.ink}}>New chat</div>
          </div>
          <div style={{padding: '22px 30px'}}>
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 22px', borderRadius: 14, border: `1.5px solid ${menu > 0 ? C.terracotta : C.cardLine}`}}>
              <div style={{fontWeight: 700, fontSize: 32, color: pick ? C.ink : C.inkSoft}}>{pick ? 'Local' : 'Choose environment'}</div>
              <svg width={26} height={26} viewBox="0 0 24 24">
                <path d="M6 9 L12 15 L18 9" stroke={C.inkSoft} strokeWidth={2.6} fill="none" strokeLinecap="round" />
              </svg>
            </div>
            <div style={{height: menu * 236, overflow: 'hidden'}}>
              {rows.map(([a, b], i) => (
                <div
                  key={a}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 18,
                    marginTop: 12,
                    padding: '16px 22px',
                    borderRadius: 14,
                    background: i === 0 && pick ? 'rgba(203,96,62,0.12)' : '#F7F5F2',
                  }}
                >
                  <div style={{flex: 1}}>
                    <div style={{fontWeight: 800, fontSize: 32, letterSpacing: '-0.03em', color: C.ink}}>{a}</div>
                    <div style={{fontWeight: 600, fontSize: 24, color: C.inkSoft}}>{b}</div>
                  </div>
                  {i === 0 && pick && <Check size={44} />}
                </div>
              ))}
            </div>
            {read > 0 && (
              <div style={{display: 'flex', alignItems: 'center', gap: 12, marginTop: 16, fontWeight: 700, fontSize: 28, color: C.terracotta, opacity: Math.min(1, read * 1.5)}}>
                <Check size={34} k={read} />
                Claude can read your files
              </div>
            )}
          </div>
        </Card>
      </div>
      {icon > 0 && (
        <>
          <div style={abs(300, 1020, popStyle(icon))}>
            <ClaudeIcon size={170} />
          </div>
          <Label text="Claude" size={42} style={abs(300, 1150, {opacity: icon})} />
          <DottedPath d="M 410 1020 L 640 1020" p={line} w={1080} h={1920} arrow={{x: 640, y: 1020, angle: 0}} />
          <div style={abs(790, 1020, popStyle(fold, 0.7))}>
            <Folder w={200} />
          </div>
          <Label text="AI Video Editor" size={38} style={abs(790, 1150, {opacity: fold})} />
        </>
      )}
    </AbsoluteFill>
  );
};

// Body 6 and 7, split: Step 2. The tool links card, then the install prompt typing in and sending.
const TOOLS: [string, string, string][] = [
  ['Remotion', 'motion graphics in code', 'remotion.dev'],
  ['FFmpeg', 'cuts, audio, export', 'ffmpeg.org'],
  ['Whisper', 'word-timed captions', 'github.com/openai/whisper'],
  ['yt-dlp', 'downloads reference reels', 'github.com/yt-dlp/yt-dlp'],
];
export const InstallTools: React.FC<P> = ({t}) => {
  const t0 = K(6);
  const card = pop(t, w('links', 6) - 0.05, 220);
  const swap = K(7);
  const prompt = pop(t, w('prompt', 7) - 0.6, 220);
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={2} title="Install the tools" y={90} k={ease(t, t0, t0 + 0.18)} />
      {t < swap && card > 0 && (
        <div style={abs(540, 520, popStyle(card, 0.8))}>
          <Card style={{width: 900}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 14, padding: '20px 30px', borderBottom: `1.5px solid ${C.cardLine}`}}>
              <Starburst size={36} color={C.terracotta} />
              <div style={{fontWeight: 800, fontSize: 36, letterSpacing: '-0.03em', color: C.ink}}>Install these tools</div>
            </div>
            {TOOLS.map(([n, d, link], i) => {
              const k = ease(t, w('required', 6) + i * 0.12, w('required', 6) + i * 0.12 + 0.2);
              return (
                <div key={n} style={{display: 'flex', alignItems: 'center', padding: '14px 30px', borderTop: i ? `1.5px solid ${C.cardLine}` : undefined, opacity: k, translate: `${(1 - k) * 30}px 0`}}>
                  <div style={{width: 300}}>
                    <div style={{fontWeight: 800, fontSize: 34, letterSpacing: '-0.03em', color: C.ink}}>{n}</div>
                    <div style={{fontWeight: 600, fontSize: 22, color: C.inkSoft}}>{d}</div>
                  </div>
                  <div style={{flex: 1, fontWeight: 700, fontSize: 26, color: '#2F7FC1', textDecoration: 'underline'}}>{link}</div>
                </div>
              );
            })}
          </Card>
        </div>
      )}
      {t >= swap && (
        <div style={abs(540, 520, popStyle(Math.max(prompt, pop(t, swap)), 0.8))}>
          <PromptCard
            t={t}
            t0={swap}
            lines={['Install these tools on my computer:', '1. Remotion  2. FFmpeg  3. Whisper  4. yt-dlp', 'Test each one, then tell me when you are ready.']}
            send={w('prompt', 7) + 0.1}
          />
        </div>
      )}
    </AbsoluteFill>
  );
};

// Body 8 and 9, split: Step 3. A colour fan for "style", someone's reels, 3 to 4 of them fly to Claude, then
// the style prompt.
export const FindStyle: React.FC<P> = ({t}) => {
  const t0 = K(8);
  const fan = pop(t, w('style', 8));
  const reels = w('copy', 8);
  const send = w('send', 8);
  const fly = ease(t, w('examples', 8), w('claude', 8) + 0.1);
  const icon = pop(t, w('reels', 8) - 0.1);
  const mim = pop(t, w('mimic', 8));
  const own = pop(t, at('own', w('mimic', 8)));
  const promptAt = K(9);
  const fanOut = ease(t, reels - 0.1, reels + 0.15);
  const COLORS = ['#E8574A', '#F08A3C', '#F4C343', '#8CC56A', '#4FB6C9', '#5679D1', '#9364C8'];
  if (t >= promptAt) {
    return (
      <AbsoluteFill>
        <Paper style={{height: 960}} />
        <StepHeader n={3} title="Find your style" y={90} k={1} />
        <div style={abs(540, 520, popStyle(pop(t, promptAt), 0.85))}>
          <PromptCard t={t} t0={promptAt - 0.3} lines={['Learn the editing style from these videos:', '[LINK 1]  [LINK 2]  [LINK 3]', 'Study the cuts, captions and graphics.']} />
        </div>
      </AbsoluteFill>
    );
  }
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={3} title="Find your style" y={90} k={ease(t, t0, t0 + 0.18)} />
      {fanOut < 1 &&
        COLORS.map((c, i) => (
          <div
            key={c}
            style={{
              position: 'absolute',
              left: 540 - 40,
              top: 640,
              width: 80,
              height: 330,
              borderRadius: 14,
              background: c,
              border: '4px solid #fff',
              transformOrigin: '50% 90%',
              transform: `translateY(-100%) rotate(${(i - 3) * 16 * fan}deg)`,
              boxShadow: '0 4px 10px rgba(0,0,0,0.15)',
              opacity: Math.min(1, fan * 1.6) * (1 - fanOut),
            }}
          />
        ))}
      {[0, 1, 2].map((i) => {
        const k = pop(t, reels + i * 0.12);
        if (k <= 0) return null;
        const x0 = 270 + i * 270;
        const x = mix(x0, 830, fly);
        const y = mix(470, 470, fly) - Math.sin(fly * Math.PI) * 120;
        return (
          <div key={i} style={abs(x, y, {...popStyle(k, 0.7), scale: `${mix(1, 0.25, fly)}`, opacity: fly >= 1 ? 0 : 1, rotate: `${(i - 1) * 5}deg`})}>
            <ReelCard src={`assets/reel${i + 1}.mp4`} t0={reels} w={180} />
          </div>
        );
      })}
      {t >= send - 0.05 && fly < 1 && <Label text="3-4 examples" color={C.terracotta} size={44} style={abs(540, 790, {opacity: ease(t, send, send + 0.2)})} />}
      {icon > 0 && fly > 0 && (
        <>
          <div style={abs(830, 470, popStyle(icon))}>
            <div style={{scale: `${1 + 0.1 * Math.sin(Math.min(1, Math.max(0, (t - w('claude', 8) - 0.1) / 0.25)) * Math.PI)}`}}>
              <ClaudeIcon size={210} />
            </div>
          </div>
          <Label text="Claude" size={44} style={abs(830, 640, {opacity: icon})} />
        </>
      )}
      {mim > 0 && (
        <div style={abs(330, 470, {textAlign: 'center', ...popStyle(mim, 0.7)})}>
          <Label text="Mimic their style" size={48} />
          <div style={{display: 'flex', justifyContent: 'center', marginTop: 16}}>
            <Check size={56} k={mim} />
          </div>
          {own > 0 && <Label text="or create your own" color={C.terracotta} size={42} style={{marginTop: 22, opacity: Math.min(1, own * 1.6)}} />}
        </div>
      )}
    </AbsoluteFill>
  );
};

// Body 10 and 11, split: Step 4. A camera frame records on "film", the raw clips line up (cuts and all),
// then drop into the Raw footage folder.
export const FilmIt: React.FC<P> = ({t}) => {
  const t0 = K(10);
  const cam = pop(t, w('film', 10));
  const raws = w('raw', 10);
  const cuts = pop(t, w('cuts', 10));
  const t1 = K(11);
  const fold = pop(t, w('place', 11) - 0.1);
  const drop = ease(t, w('footage', 11), w('footage', 11) + 0.45);
  const tick = pop(t, w('subfolder', 11));
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={4} title="Film and edit" y={90} k={ease(t, t0, t0 + 0.18)} />
      {t < t1 && cam > 0 && (
        <div style={abs(540, raws <= t ? 330 : 470, popStyle(cam, 0.7))}>
          <div style={{width: 200, height: 300, borderRadius: 26, border: '6px solid #2A2522', background: '#3A3430', position: 'relative', boxShadow: '0 10px 24px rgba(0,0,0,0.2)'}}>
            <div style={{position: 'absolute', top: 18, left: 18, display: 'flex', alignItems: 'center', gap: 8, fontFamily: FONT, fontWeight: 800, fontSize: 24, color: '#fff'}}>
              <div style={{width: 18, height: 18, borderRadius: 9, background: '#E8574A', opacity: Math.floor(t * 2.5) % 2 ? 0.3 : 1}} />
              REC
            </div>
            <div style={abs(100, 160, {width: 74, height: 74, borderRadius: 40, border: '6px solid rgba(255,255,255,0.8)'})} />
          </div>
        </div>
      )}
      {t < t1 &&
        [0, 1, 2].map((i) => {
          const k = pop(t, raws + 0.1 + i * 0.1);
          if (k <= 0) return null;
          return (
            <div key={i} style={abs(300 + i * 240, 640, popStyle(k, 0.7))}>
              <ReelCard src={`assets/raw${i + 1}.jpg`} t0={0} w={110} style={{rotate: `${(i - 1) * 4}deg`}} />
            </div>
          );
        })}
      {t < t1 && cuts > 0 && <Label text="keep all the cuts" color={C.terracotta} size={44} style={abs(540, 820, popStyle(cuts, 0.7))} />}
      {t >= t1 && (
        <>
          <div style={abs(540, 520, popStyle(fold, 0.7))}>
            <Folder w={340} open={0.5}>
              {[0, 1, 2].map((i) => (
                <Img
                  key={i}
                  src={staticFile(`assets/raw${i + 1}.jpg`)}
                  style={{position: 'absolute', left: 70 + i * 70, top: mix(-380, -30 + (i === 1 ? -14 : 0), drop), width: 90, height: 136, objectFit: 'cover', border: '4px solid #fff', borderRadius: 6, rotate: `${(i - 1) * 6}deg`, opacity: drop > 0 ? 1 : 0}}
                />
              ))}
            </Folder>
          </div>
          <div style={abs(540, 735, {display: 'flex', alignItems: 'center', gap: 16, ...popStyle(fold, 0.7)})}>
            <Label text="Raw footage" color={C.terracotta} size={50} />
            <Check size={50} k={tick} />
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};

// Body 12, split: Step 4. The edit prompt sends, then cuts, captions and music line up on his words.
const Item: React.FC<{k: number; label: string; children: React.ReactNode}> = ({k, label, children}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18, ...popStyle(k, 0.6)}}>
    <div style={{width: 190, height: 190, borderRadius: 40, background: '#fff', boxShadow: '0 12px 28px rgba(40,30,20,0.18)', display: 'flex', alignItems: 'center', justifyContent: 'center'}}>{children}</div>
    <Label text={label} size={42} />
  </div>
);
export const EditPrompt: React.FC<P> = ({t}) => {
  const t0 = K(12);
  const card = pop(t, w('prompt', 12) - 0.3, 220);
  const send = w('entire', 12) + 0.1;
  const items = [w('captions', 12), w('cuts', 12), w('music', 12)];
  const out = ease(t, items[0] - 0.2, items[0]);
  const all = pop(t, w('everything', 12));
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <StepHeader n={4} title="Film and edit" y={90} k={1} />
      {out < 1 && card > 0 && (
        <div style={abs(540, 510, {...popStyle(card, 0.8), opacity: Math.min(1, card * 1.6) * (1 - out)})}>
          <PromptCard t={t} t0={t0} lines={['Edit my new video in the Raw footage folder.', 'Cut the pauses, add captions and music.', 'Show me a storyboard to review first.']} send={send} />
        </div>
      )}
      {out > 0 && (
        <div style={abs(540, 500, {display: 'flex', gap: 60})}>
          <Item k={pop(t, items[0])} label="Captions">
            <div style={{fontFamily: FONT, fontWeight: 900, fontSize: 64, color: C.ink, border: `7px solid ${C.ink}`, borderRadius: 18, padding: '0 14px', letterSpacing: '-0.04em'}}>CC</div>
          </Item>
          <Item k={pop(t, items[1])} label="Cuts">
            <svg width={110} height={110} viewBox="0 0 24 24">
              <circle cx={6} cy={6} r={3} stroke={C.terracotta} strokeWidth={2} fill="none" />
              <circle cx={6} cy={18} r={3} stroke={C.terracotta} strokeWidth={2} fill="none" />
              <path d="M8.5 7.5 L20 18 M8.5 16.5 L20 6" stroke={C.ink} strokeWidth={2} strokeLinecap="round" />
            </svg>
          </Item>
          <Item k={pop(t, items[2])} label="Music">
            <svg width={100} height={100} viewBox="0 0 24 24">
              <path d="M9 18 V5 L20 3 V16" stroke={C.ink} strokeWidth={2.2} fill="none" strokeLinejoin="round" />
              <circle cx={6.5} cy={18} r={2.6} fill={C.folderDeep} />
              <circle cx={17.5} cy={16} r={2.6} fill={C.folderDeep} />
            </svg>
          </Item>
        </div>
      )}
      {all > 0 && (
        <div style={abs(540, 790, {display: 'flex', alignItems: 'center', gap: 16, ...popStyle(all, 0.7)})}>
          <Check size={54} k={all} />
          <Label text="Everything, done by Claude" size={46} />
        </div>
      )}
    </AbsoluteFill>
  );
};

// Body 13, face: a small chat above his head, his note and Claude's "Done."
export const Adjust: React.FC<P> = ({t}) => {
  const ask = pop(t, w('adjustment', 13) - 0.2, 220);
  const done = pop(t, w('tell', 13), 220);
  if (ask <= 0) return null;
  return (
    <div style={abs(540, 470, {width: 820, ...popStyle(ask, 0.8)})}>
      <Card style={{padding: '22px 26px'}}>
        <div style={{display: 'flex', justifyContent: 'flex-end'}}>
          <div style={{background: '#EFEBE5', borderRadius: 18, padding: '12px 22px', fontWeight: 700, fontSize: 32, color: C.ink}}>Make the captions bigger</div>
        </div>
        {done > 0 && (
          <div style={{display: 'flex', alignItems: 'center', gap: 14, marginTop: 18, opacity: Math.min(1, done * 1.6)}}>
            <Starburst size={36} color={C.terracotta} />
            <div style={{fontWeight: 700, fontSize: 32, color: C.ink}}>Done. Captions are bigger now.</div>
          </div>
        )}
      </Card>
    </div>
  );
};

// Body 14 and 15, full paper: the recap. The AI Video Editor folder in the middle, the four steps point in.
export const Recap: React.FC<P> = ({t}) => {
  const t0 = K(14);
  const solid = ease(t, t0 + 0.05, t0 + 0.25);
  const reel = pop(t, w('reel', 14), 240);
  const corners = [
    {x: 260, y: 470, n: 'Step 1.', s: 'Set it up', d: 'M 280 540 C 300 610, 340 660, 405 698', a: {x: 405, y: 698, angle: 40}},
    {x: 820, y: 470, n: 'Step 2.', s: 'Install the tools', d: 'M 800 540 C 780 610, 740 660, 675 698', a: {x: 675, y: 698, angle: 140}},
    {x: 260, y: 1150, n: 'Step 3.', s: 'Find your style', d: 'M 280 1085 C 300 1010, 330 960, 385 930', a: {x: 385, y: 930, angle: -35}},
    {x: 820, y: 1150, n: 'Step 4.', s: 'Film and edit', d: 'M 800 1085 C 780 1010, 750 960, 695 930', a: {x: 695, y: 930, angle: -145}},
  ];
  return (
    <AbsoluteFill>
      <Paper />
      <div style={abs(540, 810)}>
        <Folder w={320} solid={solid} />
      </div>
      <Label text="AI Video Editor" size={46} style={abs(540, 985, {opacity: solid})} />
      {corners.map((c, i) => {
        const t1 = t0 + 0.12 + i * 0.25;
        const k = pop(t, t1);
        return (
          <React.Fragment key={i}>
            <div style={abs(c.x, c.y, {textAlign: 'center', ...popStyle(k, 0.7)})}>
              <Label text={c.n} color={C.terracotta} size={46} />
              <Label text={c.s} size={48} />
            </div>
            <DottedPath d={c.d} p={ease(t, t1 + 0.08, t1 + 0.4)} w={1080} h={1920} dot={6} arrow={c.a} />
          </React.Fragment>
        );
      })}
      {reel > 0 && (
        <div style={abs(540, 790, {...popStyle(reel, 0.5), rotate: '-4deg'})}>
          <ReelCard src="assets/reel1.mp4" t0={w('reel', 14)} w={190} />
        </div>
      )}
    </AbsoluteFill>
  );
};

// Body 16, split: his own workflow folder, FREE stamped on "free", a reel of his on "like this".
export const Workflow: React.FC<P> = ({t}) => {
  const t0 = K(16);
  const fold = pop(t, w('workflow', 16) - 0.3);
  const stamp = pop(t, w('free', 16), 260);
  const reel = pop(t, w('videos', 16));
  return (
    <AbsoluteFill>
      <Paper style={{height: 960}} />
      <div style={abs(reel > 0 ? 360 : 540, 450, popStyle(fold, 0.7))}>
        <Folder w={300} />
      </div>
      <Label text="My editing workflow" size={46} style={abs(reel > 0 ? 360 : 540, 640, {opacity: Math.min(1, fold * 1.5)})} />
      {stamp > 0 && (
        <div
          style={abs(reel > 0 ? 360 : 540, 440, {
            padding: '8px 36px',
            borderRadius: 20,
            background: C.terracotta,
            color: '#fff',
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: 90,
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
      {reel > 0 && (
        <div style={abs(790, 470, {...popStyle(reel, 0.6), rotate: '4deg'})}>
          <ReelCard src="assets/reel2.mp4" t0={w('videos', 16)} w={220} />
        </div>
      )}
    </AbsoluteFill>
  );
};

// Body 17, face: his CTA. A white pill types MOTION, the arrow button goes dark.
export const Cta: React.FC<P> = ({t}) => {
  const word = 'MOTION';
  const t0 = w('motion', 17);
  const k = pop(t, K(17) + 0.1, 220);
  const typed = Math.max(0, Math.min(word.length, Math.floor((t - t0) / 0.07) + 1));
  const done = t >= t0 + word.length * 0.07 + 0.08;
  const caret = !done && Math.floor(t * 4) % 2 === 0;
  if (k <= 0) return null;
  return (
    <div
      style={abs(540, 470, {
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
          scale: done ? `${mix(1.15, 1, ease(t, t0 + 0.5, t0 + 0.7))}` : '1',
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
export const NAMES = ['Claude', 'Code', 'AI', 'Video', 'Editor'];

// Hard cuts between his three layouts, each at the start of a take.
export const SCENES: Scene[] = [
  {from: 0, to: K(0), layout: 'face', Graphic: Hook},
  {from: K(0), to: K(1), layout: 'split', Graphic: DesktopApp},
  {from: K(1), to: K(2), layout: 'full', captionY: 0.68, Graphic: CreateFolder},
  {from: K(2), to: K(5), layout: 'split', Graphic: Subfolders},
  {from: K(5), to: K(6), layout: 'full', captionY: 0.73, Graphic: ClaudeChat},
  {from: K(6), to: K(8), layout: 'split', Graphic: InstallTools},
  {from: K(8), to: K(10), layout: 'split', Graphic: FindStyle},
  {from: K(10), to: K(12), layout: 'split', Graphic: FilmIt},
  {from: K(12), to: K(13), layout: 'split', Graphic: EditPrompt},
  {from: K(13), to: K(14), layout: 'face', Graphic: Adjust},
  {from: K(14), to: K(16), layout: 'full', captionY: 0.73, Graphic: Recap},
  {from: K(16), to: K(17), layout: 'split', Graphic: Workflow},
  {from: K(17), to: 999, layout: 'face', Graphic: Cta},
];

const hookCards = H1 ? [0.02, at('editing'), at('videos')] : [0.02, at('build'), at('editor')];
// Soft pops on graphics, a light whoosh into full-paper scenes, key clicks on the typed CTA. No music.
export const SFX: Sfx[] = [
  ...hookCards.map((s): Sfx => ['pop_light_3005', s, 0.3]),
  ['whoosh_air_1489', K(0) - 0.03, 0.18],
  ['pop_light_3005', w('claude', 0), 0.35],
  ['pop_light_3005', w('browser', 0), 0.3],
  ['pop_hard_click_2364', w('version', 0), 0.25],
  ['pop_dry_2356', w('version', 0) + 0.2, 0.35],
  ['whoosh_fast_1490', K(1) - 0.03, 0.3],
  ['pop_light_3005', w('folder', 1) - 0.1, 0.3],
  ['pop_dry_2356', w('called', 1) + 0.15, 0.35],
  ['whoosh_air_1489', K(2) - 0.03, 0.18],
  ['pop_light_3005', w('subfolders', 2), 0.3],
  ['pop_light_3005', w('raw', 3), 0.3],
  ['pop_light_3005', w('references', 3), 0.3],
  ['pop_light_3005', w('exports', 3), 0.3],
  ['whoosh_fast_1490', K(5) - 0.03, 0.3],
  ['pop_light_3005', K(5) + 0.05, 0.3],
  ['pop_hard_click_2364', w('select', 5), 0.25],
  ['pop_dry_2356', w('local', 5) + 0.15, 0.35],
  ['pop_light_3005', w('point', 5), 0.3],
  ['pop_light_3005', w('folder', 5) - 0.15, 0.3],
  ['whoosh_air_1489', K(6) - 0.03, 0.18],
  ['pop_light_3005', w('links', 6) - 0.05, 0.3],
  ['pop_light_3005', K(7), 0.25],
  ['pop_hard_click_2364', w('prompt', 7) + 0.1, 0.3],
  ['pop_light_3005', w('style', 8), 0.3],
  ['pop_light_3005', w('copy', 8), 0.3],
  ['whoosh_fast_1490', w('examples', 8), 0.22],
  ['pop_dry_2356', w('claude', 8) + 0.1, 0.35],
  ['pop_dry_2356', w('mimic', 8), 0.3],
  ['pop_light_3005', K(9), 0.25],
  ['pop_light_3005', w('film', 10), 0.3],
  ['pop_light_3005', w('raw', 10) + 0.1, 0.25],
  ['pop_dry_2356', w('cuts', 10), 0.3],
  ['pop_light_3005', w('place', 11) - 0.1, 0.3],
  ['pop_dry_2356', w('footage', 11) + 0.45, 0.35],
  ['pop_light_3005', w('prompt', 12) - 0.3, 0.3],
  ['pop_hard_click_2364', w('entire', 12) + 0.1, 0.3],
  ['pop_light_3005', w('captions', 12), 0.3],
  ['pop_light_3005', w('cuts', 12), 0.3],
  ['pop_light_3005', w('music', 12), 0.3],
  ['lab_ding', w('everything', 12), 0.2],
  ['pop_light_3005', w('adjustment', 13) - 0.2, 0.3],
  ['pop_dry_2356', w('tell', 13), 0.3],
  ['whoosh_fast_1490', K(14) - 0.03, 0.3],
  ['pop_light_3005', K(14) + 0.12, 0.25],
  ['pop_light_3005', K(14) + 0.62, 0.25],
  ['pop_dry_2356', w('reel', 14), 0.35],
  ['whoosh_air_1489', K(16) - 0.03, 0.18],
  ['pop_light_3005', w('workflow', 16) - 0.3, 0.3],
  ['pop_dry_2356', w('free', 16), 0.55],
  ['pop_light_3005', w('videos', 16), 0.3],
  ['pop_light_3005', K(17) + 0.1, 0.3],
  ...[0, 1, 2, 3, 4, 5].map((i): Sfx => ['pop_hard_click_2364', w('motion', 17) + i * 0.07, 0.22]),
  ['pop_dry_2356', w('motion', 17) + 0.5, 0.3],
];

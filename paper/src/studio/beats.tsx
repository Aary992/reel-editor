// THIS REEL: "story demo" (10-10 takes, "how I analyze any stock with Claude", first studio reel 10-25).
// One component per graphics set, each with its own camera; every element lands on the word that names it
// (`at`). SCENES, SFX and CTA at the bottom drive the generic Studio.tsx.
import React from 'react';
import {ArcList, ChartThumb, Chips, FileChip, Greeting, Heading, InputBox, KineticLine, Note, Pill, Place, Rating, Reply, ScoreSheet, Sheet, Thinking, UserBubble, World, enter, kineticLayout} from './kit';
import type {Cam, Key, KWord} from './kit';
import {at} from './data';
import type {Cta, Scene, Sfx} from './data';
import {clamp, mix, pop} from './style';

type P = {t: number};

// ---------- times ----------

const T = {
  step1: at('step'),                    // 3.43
  upload: at('upload'),                 // 5.95
  claude1: at('claude', 7),             // 8.07 send
  explains: at('explains'),             // 8.59
  and1: at('and', 10),                  // 10.11, back to his face
  step2: at('step', 14),                // 14.19
  give: at('i', 16),                    // 16.55
  ten: at('10', 17),                    // 17.35
  again: at('again'),                   // 19.43
  score: at('score', 20),               // 20.41
  only: at('only', 21),                 // 21.43
  six: at('6'),                         // 23.45
  look: at('look', 24),                 // 24.65
  step3: at('step', 25.5),              // 25.74
  send: at('i', 27.5),                  // 27.64
  daily: at('daily'),                   // 28.54
  weekly: at('weekly'),                 // 29.34
  fully: at('it', 30.9),                // 30.98
  trend: at('trend'),                   // 34.01
  key: at('key'),                       // 35.07
  volume: at('volume'),                 // 36.37
  every: at('every'),                   // 36.93
  one: at('one', 38),                   // 38.37
  only2: at('only', 38.8),              // 38.91
  which: at('which', 39),               // 39.15
  wait: at('wait'),                     // 39.97
  study: at('study'),                   // 40.47
  skip: at('skip'),                     // 41.45
  comment: at('comment'),               // 41.86
};

// Scene edges (seconds): face 0, board, Claude, face, board, sheet, board, Claude, arc, kinetic, face.
const E = [0, 3.4, T.upload - 0.12, T.and1 - 0.05, 14.1333, T.give, 25.4, T.send - 0.04, 33.3667, 36.8667, 41.8333, 46.0];

// ---------- the board: how I analyze any stock, three pinned notes ----------

const NOTES = [
  {n: '01', title: 'Understanding\nthe business', x: -235, y: -150, rot: -7},
  {n: '02', title: 'The\nfinancials', x: 240, y: 175, rot: 6},
  {n: '03', title: 'Technical\nanalysis', x: -215, y: 505, rot: -4},
];
const noteCam = (i: number, z: number, dy = 0, extra: Partial<Cam> = {}): Cam => ({x: NOTES[i].x, y: NOTES[i].y + 30 + dy, z, rz: NOTES[i].rot * 0.5, ...extra});

const Board: React.FC<{t: number; keys: Key[]; id: string; drop?: number; done: number[]}> = ({t, keys, id, drop, done}) => (
  <World t={t} keys={keys} id={id}>
    <Place x={0} y={-590}>
      <div style={drop === undefined ? {} : enter(t, drop, 40)}>
        <Heading size={84}>{'How I analyze\nany stock'}</Heading>
      </div>
    </Place>
    {NOTES.map((n, i) => (
      <Place key={i} x={n.x} y={n.y} rot={n.rot}>
        <div style={drop === undefined ? {} : enter(t, drop + 0.14 + i * 0.16, 90, 180)}>
          <Note n={n.n} title={n.title} done={pop(t, done[i], 260)} />
        </div>
      </Place>
    ))}
  </World>
);

const Board1: React.FC<P> = ({t}) => (
  <Board
    t={t}
    id="b1"
    drop={E[1] + 0.02}
    done={[1e9, 1e9, 1e9]}
    keys={[
      [E[1], {x: 0, y: -30, z: 0.74, rx: 12}],
      [T.step1 + 1.0, {x: -10, y: -50, z: 0.84, rx: 6}],
      [E[2] + 0.05, noteCam(0, 2.05)],
    ]}
  />
);

const Board2: React.FC<P> = ({t}) => (
  <Board
    t={t}
    id="b2"
    done={[E[4] + 0.15, 1e9, 1e9]}
    keys={[
      [E[4], noteCam(0, 1.4)],
      [T.step2 + 0.1, noteCam(0, 1.4)],
      [T.step2 + 0.9, noteCam(1, 1.4)],
      [E[5] + 0.05, noteCam(1, 2.05)],
    ]}
  />
);

const Board3: React.FC<P> = ({t}) => (
  <Board
    t={t}
    id="b3"
    done={[0, E[6] + 0.15, 1e9]}
    keys={[
      [E[6], noteCam(1, 1.4)],
      [T.step3 - 0.05, noteCam(1, 1.4)],
      [T.step3 + 0.75, noteCam(2, 1.4)],
      [E[7] + 0.05, noteCam(2, 2.05)],
    ]}
  />
);

// ---------- Claude's app ----------

// Types `text` between t0 and t1, one character at a time.
const typed = (t: number, text: string, t0: number, t1: number) => text.slice(0, Math.round(clamp((t - t0) / (t1 - t0)) * text.length));
// The send button goes down and back up around t0.
const press = (t: number, t0: number) => clamp(1 - Math.abs(t - t0 - 0.06) / 0.09);
// Something dropped into the prompt box: flies in from the bottom right, lands with a bounce.
const fly = (t: number, t0: number): React.CSSProperties => {
  const k = pop(t, t0, 170);
  return {opacity: clamp(k * 2), transform: `translate(${(1 - k) * 280}px, ${(1 - k) * 420}px) rotate(${(1 - k) * 14}deg) scale(${mix(1.25, 1, k)})`};
};

const THREAD = 1450;   // the conversation sits below the home screen; the camera whips down to it on send

const LINES = ['What the company sells', 'Who its customers are', 'How it makes money', "Where it's growing", 'Who it competes with', 'What could go wrong'];

// 5.8 to 10.1 s: "I upload the investor presentation and Claude explains it to me in six lines".
const Claude1: React.FC<P> = ({t}) => {
  const prompt = 'Explain this business in 6 lines';
  const sent = t >= T.claude1 + 0.06;
  return (
    <World
      t={t}
      id="c1"
      keys={[
        [E[2], {x: 0, y: 10, z: 1.12, rx: 10, ry: -7}],
        [T.claude1, {x: 0, y: 0, z: 1.28, rx: 6, ry: -3}],
        [T.claude1 + 0.45, {x: 0, y: THREAD + 40, z: 1.32, rx: 4, ry: 3}],
        [E[3] + 0.3, {x: 0, y: THREAD + 150, z: 1.42, rx: 2, ry: 5}],
      ]}
    >
      <Place x={0} y={-250}>
        <Greeting text="Let's dig in, Aarit" spin={t * 6} />
      </Place>
      <Place x={0} y={20}>
        <InputBox
          text={sent ? '' : typed(t, prompt, T.upload + 0.75, T.claude1 - 0.12)}
          caret={!sent && t > T.upload + 0.6 && Math.floor(t * 3) % 2 === 0}
          press={press(t, T.claude1)}
          attach={
            <div style={sent ? {opacity: 0} : fly(t, T.upload + 0.03)}>
              <FileChip name="Investor presentation" />
            </div>
          }
        />
      </Place>
      <Place x={0} y={300}>
        <Chips items={['Write', 'Learn', 'Code', 'Analyze']} />
      </Place>
      <Place x={95} y={THREAD - 270}>
        <div style={enter(t, T.claude1 + 0.12, 30)}>
          <UserBubble>
            <FileChip name="Investor presentation" />
            <div>{prompt}</div>
          </UserBubble>
        </div>
      </Place>
      <Place x={20} y={THREAD + 150}>
        <Reply
          w={680}
          t={t}
          title="The business, in six lines"
          titleAt={T.claude1 + 0.4}
          spin={t * 20}
          lines={LINES.map((text, i) => ({text, at: T.explains + 0.03 + i * 0.235}))}
        />
      </Place>
    </World>
  );
};

// 27.6 to 33.4 s: "I send Claude the daily and the weekly chart of the stock and it fully analyzes it".
const Claude2: React.FC<P> = ({t}) => {
  const prompt = 'Analyze both charts';
  const sent = t >= T.fully + 0.06;
  const charts = (live: boolean) => (
    <>
      <div style={live ? fly(t, T.daily + 0.02) : {}}>
        <ChartThumb label="Daily" seed={11} trend={-0.6} />
      </div>
      <div style={live ? fly(t, T.weekly + 0.02) : {}}>
        <ChartThumb label="Weekly" seed={5} trend={1.1} />
      </div>
    </>
  );
  return (
    <World
      t={t}
      id="c2"
      keys={[
        [E[7], {x: 0, y: 30, z: 1.12, rx: 10, ry: 7}],
        [T.fully, {x: 0, y: 40, z: 1.28, rx: 6, ry: 3}],
        [T.fully + 0.45, {x: 0, y: THREAD, z: 1.32, rx: 4, ry: -3}],
        [E[8] + 0.3, {x: 0, y: THREAD + 90, z: 1.4, rx: 2, ry: -5}],
      ]}
    >
      <Place x={0} y={-290}>
        <Greeting text="Back at it, Aarit" spin={t * 6} />
      </Place>
      <Place x={0} y={30}>
        <InputBox
          text={sent ? '' : typed(t, prompt, T.weekly + 0.45, T.fully - 0.2)}
          caret={!sent && t > T.weekly + 0.35 && Math.floor(t * 3) % 2 === 0}
          press={press(t, T.fully)}
          attach={<div style={{display: 'flex', gap: 16, opacity: sent ? 0 : 1}}>{charts(true)}</div>}
        />
      </Place>
      <Place x={0} y={360}>
        <Chips items={['Write', 'Learn', 'Code', 'Analyze']} />
      </Place>
      <Place x={60} y={THREAD - 330}>
        <div style={enter(t, T.fully + 0.12, 30)}>
          <UserBubble>
            <div style={{display: 'flex', gap: 14}}>{charts(false)}</div>
            <div>{prompt}</div>
          </UserBubble>
        </div>
      </Place>
      <Place x={20} y={THREAD + 190}>
        <Thinking t={t} t0={T.fully + 0.4} label="Reading the daily and weekly chart" spin={t * 40} w={680} />
      </Place>
    </World>
  );
};

// ---------- 16.5 to 25.4 s: ten years of financials, then the score sheet and his line at 6 ----------

const YEARS = ['FY16', 'FY17', 'FY18', 'FY19', 'FY20', 'FY21', 'FY22', 'FY23', 'FY24', 'FY25'];
const SCORE_Y = 1150;

const Financials: React.FC<P> = ({t}) => (
  <World
    t={t}
    id="fin"
    keys={[
      [E[5], {x: -330, y: -40, z: 1.32, rx: 16, ry: 12}],
      [T.ten - 0.05, {x: -320, y: -30, z: 1.34, rx: 12, ry: 9}],
      [T.ten + 1.5, {x: 330, y: -20, z: 1.34, rx: 10, ry: -9}],
      [T.ten + 2.05, {x: 0, y: 0, z: 0.95, rx: 8, ry: 0}],
      [T.again + 0.3, {x: 0, y: 30, z: 0.97, rx: 8, ry: 0}],
      [T.score + 0.05, {x: 0, y: SCORE_Y + 30, z: 1.15, rx: 6, ry: 0}],
      [T.only + 0.1, {x: 0, y: SCORE_Y + 60, z: 1.15, rx: 4, ry: -2}],
      [T.six - 0.4, {x: 0, y: SCORE_Y + 560, z: 1.08, rx: 3, ry: -3}],
      [E[6] + 0.3, {x: 0, y: SCORE_Y + 590, z: 1.12, rx: 2, ry: -3}],
    ]}
  >
    <Place x={0} y={0}>
      <Sheet t={t} title="10 years of financials" titleAt={T.ten} years={YEARS} cols={YEARS.map((_, j) => T.ten + j * 0.095)} rows={['Revenue', 'Net profit', 'Margins', 'Debt', 'Cash flow', 'Return on equity']} />
    </Place>
    <Place x={0} y={SCORE_Y}>
      <ScoreSheet
        t={t}
        title="Score sheet"
        titleAt={T.score}
        rows={[
          {label: 'Growth', v: 8},
          {label: 'Profitability', v: 7},
          {label: 'Debt', v: 6},
          {label: 'Cash flow', v: 8},
          {label: 'Valuation', v: 5},
        ].map((r, i) => ({...r, at: T.score + 0.08 + i * 0.13}))}
      />
    </Place>
    <Place x={0} y={SCORE_Y + 470}>
      <Rating t={t} t0={T.only} lineAt={T.six} fillFrom={T.six + 0.15} fillTo={T.six + 0.95} to={0.74} />
    </Place>
    <Place x={0} y={SCORE_Y + 650}>
      <div style={enter(t, T.look, 40, 260)}>
        <Pill text="Worth a look" check dark />
      </div>
    </Place>
  </World>
);

// ---------- 33.4 to 36.9 s: "whether the trend agrees, the key levels and the volume" ----------

const ARC_R = 1400;
const ARC_GAP = 17;
const arcY = (i: number) => ARC_R * Math.sin(((i - 1) * ARC_GAP * Math.PI) / 180);

const Checks: React.FC<P> = ({t}) => (
  <World
    t={t}
    id="arc"
    keys={[
      [E[8], {x: 0, y: arcY(0) - 30, z: 1.22, rx: 6, ry: -16, rz: -5}],
      [T.trend + 0.2, {x: 20, y: arcY(0), z: 1.3, rx: 5, ry: -13, rz: -4}],
      [T.key + 0.05, {x: 20, y: arcY(1), z: 1.3, rx: 4, ry: -11, rz: 0}],
      [T.volume + 0.05, {x: 20, y: arcY(2), z: 1.3, rx: 4, ry: -9, rz: 4}],
      [E[9] + 0.3, {x: 30, y: arcY(2) - 20, z: 1.36, rx: 4, ry: -8, rz: 4}],
    ]}
  >
    <div style={{position: 'absolute', left: -260, top: 0}}>
      <ArcList
        t={t}
        R={ARC_R}
        gap={ARC_GAP}
        items={[
          {label: 'Trend agrees?', at: T.trend, dot: E[8] + 0.05},
          {label: 'Key levels', at: T.key, dot: E[8] + 0.17},
          {label: 'Volume', at: T.volume, dot: E[8] + 0.29},
        ]}
      />
    </div>
  </World>
);

// ---------- 36.9 to 41.8 s: "Every stock ends with one word only, which is either wait, study or skip" ----------

const LINE1: KWord[] = [
  {text: 'Every', at: T.every},
  {text: 'stock', at: at('stock', 37)},
  {text: 'ends', at: at('ends')},
  {text: 'with', at: at('with', 38)},
  {text: 'one word', at: T.one, hl: T.one + 0.06},
  {text: 'only', at: T.only2},
];
const LINE2: KWord[] = [
  {text: 'Wait', at: T.wait, hl: T.wait + 0.03, off: T.study},
  {text: 'Study', at: T.study, hl: T.study + 0.03, off: T.skip},
  {text: 'Skip', at: T.skip, hl: T.skip + 0.03},
];
const S1 = 96;
const S2 = 132;
const C1 = kineticLayout(LINE1, S1);
const C2 = kineticLayout(LINE2, S2);
const ROW2 = {x: C1[C1.length - 1] - 260, y: 300};

// The camera pans along the line at one even speed, from the first word to the last, like his: each new
// word appears a little right of centre and slides in as the camera arrives.
const pan = (centres: number[], t0: number, t1: number, cam: Omit<Cam, 'x'>): Key[] => [
  [t0, {...cam, x: centres[0] + 60}],
  [t1, {...cam, x: centres[centres.length - 1]}, 'lin'],
];

const OneWord: React.FC<P> = ({t}) => (
  <World
    t={t}
    id="kin"
    keys={[
      [E[9], {x: C1[0] + 60, y: 0, z: 0.92, rx: 4, ry: -12}],
      ...pan(C1, T.every, T.only2 + 0.25, {y: 0, z: 0.92, rx: 4, ry: -12}),
      [T.which, {x: C1[C1.length - 1] + 10, y: 0, z: 0.92, rx: 4, ry: -12}],
      [T.wait - 0.05, {x: ROW2.x, y: ROW2.y - 40, z: 0.86, rx: 4, ry: -4}],
      [E[10] + 0.1, {x: ROW2.x, y: ROW2.y - 30, z: 0.93, rx: 2, ry: -2}],
    ]}
  >
    <div style={{position: 'absolute', left: 0, top: 0, transform: 'translateY(-50%)'}}>
      <KineticLine t={t} words={LINE1} size={S1} />
    </div>
    <Place x={ROW2.x} y={ROW2.y}>
      <KineticLine t={t} words={LINE2} size={S2} weight={600} />
    </Place>
  </World>
);

// ---------- the reel ----------

export const SCENES: Scene[] = [
  {from: E[0], to: E[1], face: true},
  {from: E[1], to: E[2], Set: Board1},
  {from: E[2], to: E[3], Set: Claude1},
  {from: E[3], to: E[4], face: true},
  {from: E[4], to: E[5], Set: Board2},
  {from: E[5], to: E[6], Set: Financials},
  {from: E[6], to: E[7], Set: Board3},
  {from: E[7], to: E[8], Set: Claude2},
  {from: E[8], to: E[9], Set: Checks},
  {from: E[9], to: E[10], Set: OneWord},
  {from: E[10], to: E[11], face: true},
];

export const CTA: Cta = {from: T.comment, pill: at('claude', T.comment), to: at('all', T.comment), word: 'CLAUDE'};

export const SFX: Sfx[] = [
  ['whoosh_air_1489', E[1] - 0.08, 0.45],
  ['pop_light_3005', E[1] + 0.16, 0.45],
  ['pop_light_3005', E[1] + 0.32, 0.4],
  ['pop_light_3005', E[1] + 0.48, 0.4],
  ['whoosh_fast_1490', E[2] - 0.2, 0.4],
  ['pop_dry_2356', T.upload + 0.05, 0.55],
  ['pop_hard_click_2364', T.claude1 + 0.03, 0.5],
  ['whoosh_air_1489', T.claude1 + 0.05, 0.3],
  ...[0, 2, 4].map((i): Sfx => ['pop_light_3005', T.explains + 0.03 + i * 0.235, 0.22]),
  ['whoosh_air_1489', E[4] - 0.05, 0.4],
  ['pop_dry_2356', E[4] + 0.15, 0.45],
  ['whoosh_fast_1490', E[5] - 0.2, 0.4],
  ...[0, 3, 6, 9].map((j): Sfx => ['pop_light_3005', T.ten + j * 0.095, 0.22]),
  ['whoosh_air_1489', T.score - 0.5, 0.3],
  ['pop_light_3005', T.score + 0.08, 0.25],
  ['pop_light_3005', T.score + 0.47, 0.25],
  ['pop_dry_2356', T.six, 0.5],
  ['lab_ding', T.six + 0.75, 0.4],
  ['pop_hard_click_2364', T.look, 0.45],
  ['whoosh_fast_1490', E[6] - 0.2, 0.4],
  ['pop_dry_2356', E[6] + 0.15, 0.45],
  ['whoosh_fast_1490', E[7] - 0.2, 0.4],
  ['pop_dry_2356', T.daily + 0.05, 0.5],
  ['pop_dry_2356', T.weekly + 0.05, 0.5],
  ['pop_hard_click_2364', T.fully + 0.03, 0.5],
  ['whoosh_air_1489', T.fully + 0.05, 0.3],
  ['whoosh_fast_1490', E[8] - 0.2, 0.4],
  ['pop_light_3005', T.trend, 0.3],
  ['pop_light_3005', T.key, 0.3],
  ['pop_light_3005', T.volume, 0.3],
  ['whoosh_air_1489', E[9] - 0.2, 0.35],
  ['pop_dry_2356', T.one + 0.06, 0.45],
  ['pop_dry_2356', T.wait + 0.03, 0.45],
  ['pop_dry_2356', T.study + 0.03, 0.45],
  ['lab_boom', T.skip + 0.03, 0.75],
  ['pop_hard_click_2364', at('claude', T.comment), 0.45],
];

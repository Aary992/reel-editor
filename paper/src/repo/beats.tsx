// THIS REEL: "linkedin repo"
// One card per beat, each part landing on his exact word. Kit in kit.tsx, layout and captions in Repo.tsx.
import React from 'react';
import {at, DURATION, type Scene, type Sfx} from './data';
import {Checklist, CommentBox, Counter, RepoCard, Terminal, type Line} from './kit';
import {C} from './style';

const REPO = 'hattip-linkedin-os';

// "Someone just made a GitHub repo that using Claude makes it super easy to grow as a founder."
export const HOOK = {lines: ['100M-impression LinkedIn', 'strategy repo (free)'], to: at('if')};

const RepoBeat: React.FC<{t: number}> = ({t}) => (
  <RepoCard
    t={t}
    name={REPO}
    desc="A guided, local-first LinkedIn strategy and writing system for Claude Code."
    files={[
      ['.claude/skills', at('github') + 0.1],
      ['knowledge', at('repo') + 0.05],
      ['templates', at('that') + 0.05],
      ['CLAUDE.md', at('using')],
    ]}
  />
);

const Ready: React.FC<{t: number}> = ({t}) => (
  <Terminal
    t={t}
    lines={[
      {at: at('claude'), kind: 'prompt', text: 'Set up my LinkedIn system', secs: 0.4},
      {at: at('easy'), kind: 'claude', text: 'Your LinkedIn system is ready:'},
      {at: at('grow'), kind: 'sub', text: 'workspace/onboarding.md'},
      {at: at('as'), kind: 'sub', text: 'workspace/voice-profile.md'},
      {at: at('founder'), kind: 'sub', text: 'workspace/strategy.md'},
      {at: at('founder') + 0.2, kind: 'sub', text: 'workspace/ideas-bank.md'},
    ]}
  />
);

const Interview: React.FC<{t: number}> = ({t}) => (
  <Terminal
    t={t}
    lines={[
      {at: at('if') + 0.05, kind: 'prompt', text: 'Start my LinkedIn strategy', secs: 0.7},
      {at: at('this'), kind: 'claude', text: "What's your company website?"},
      {at: at('it', 7), kind: 'prompt', text: 'yourcompany.com', secs: 0.25},
      {at: at('interviews'), kind: 'tool', text: 'Fetch(yourcompany.com) ✓ read'},
      {at: at('interviews') + 0.25, kind: 'tool', text: 'Fetch(yourcompany.com/customers) ✓ read'},
      {at: at('you', 7.9), kind: 'tool', text: 'Fetch(yourcompany.com/pricing) ✓ read'},
      {at: at('you', 7.9) + 0.2, kind: 'claude', text: 'Got it. A few questions:'},
      {at: at('builds') - 0.05, kind: 'sub', text: '1. Who signs the contract?'},
    ]}
  />
);

const Strategy: React.FC<{t: number}> = ({t}) => {
  const s = at('builds');
  return (
    <Checklist
      t={t}
      path="workspace/strategy.md"
      title="LinkedIn Strategy"
      rows={[
        ['Ideal buyer', s + 0.15],
        ['Positioning', at('a', s) + 0.05],
        ['Content buckets', at('content', s)],
        ['Posting cadence', at('strategy', s)],
        ['Monthly calendar', at('strategy', s) + 0.3],
      ]}
    />
  );
};

const Month: React.FC<{t: number}> = ({t}) => {
  const s = at('first') + 0.2;
  const days: [string, string][] = [
    ['Mon 2', 'Why our first 10 customers almost churned'],
    ['Wed 4', '3 questions every buyer asks first'],
    ['Fri 6', 'The pricing mistake that cost us a quarter'],
    ['Mon 9', "What I'd do differently in year one"],
    ['Wed 11', 'The demo that went wrong'],
    ['Fri 13', 'How we found our first 100 users'],
    ['Mon 16', 'The hire that changed everything'],
  ];
  return (
    <Terminal
      t={t}
      lines={[
        {at: at('and', 9.5), kind: 'prompt', text: 'Plan my next month', secs: 0.45},
        {at: at('first'), kind: 'claude', text: 'Your November calendar, 3 posts a week:'},
        ...days.map(([d, x], i): Line => ({at: s + i * 0.28, kind: 'row', label: d, text: x})),
        {at: at('you', 12.5) - 0.1, kind: 'tool', text: 'Write(workspace/calendar.md) ✓ 20 posts'},
      ]}
    />
  );
};

const Data: React.FC<{t: number}> = ({t}) => (
  <Counter t={t} t0={at('backed')} from={at('over', 13)} land={at('impressions')} value={100_000_000} label="impressions" plus />
);

const Post: React.FC<{t: number}> = ({t}) => {
  const s = at('founder', 16);
  return (
    <Terminal
      t={t}
      lines={[
        {at: at('so') + 0.05, kind: 'prompt', text: 'Show me post 01', secs: 0.35},
        {at: s, kind: 'claude', text: 'Post 01 · Why our first 10 customers almost churned', bold: true},
        {at: at('just', s), kind: 'row', label: 'Stage', text: 'Top of funnel · Customer story'},
        {at: at('to', s), kind: 'row', label: 'Hook', text: 'We almost lost them in week two.'},
        {at: at('on', s), kind: 'row', label: 'Buyer', text: "Will this break when we scale?"},
        {at: at('linkedin', s), kind: 'row', label: 'CTA', text: 'Ask: what made you stay?'},
      ]}
    />
  );
};

const Review: React.FC<{t: number}> = ({t}) => {
  const s = at('or', 18);
  return (
    <Terminal
      t={t}
      lines={[
        {at: s + 0.05, kind: 'prompt', text: 'Review my draft', secs: 0.35},
        {at: at('want', s), kind: 'claude', text: 'Verdict:', badge: {text: 'Revise', color: C.amber}},
        {at: at('get', s), kind: 'sub', text: 'Lead with the number in line one'},
        {at: at('with', s), kind: 'tool', text: 'Edit(drafts/post-01.md) ✓ opening'},
        {at: at('linkedin', s) + 0.05, kind: 'claude', text: 'Verdict:', badge: {text: 'Post it', color: C.green}},
      ]}
    />
  );
};

const Recap: React.FC<{t: number}> = ({t}) => {
  const s = at('this', 21);
  return (
    <Checklist
      t={t}
      path={`claude · ${REPO}`}
      title="Your LinkedIn, sorted"
      box={{top: 230, height: 420}}
      rows={[
        ['Strategy built', s],
        ['20 posts planned', at('perfect')],
        ['Drafts reviewed', at('for', s)],
      ]}
    />
  );
};

const Cta: React.FC<{t: number}> = ({t}) => <CommentBox t={t} word="repo" typeAt={at('repo', 22)} sendAt={at('and', 22.5)} />;

export const SCENES: Scene[] = [
  {from: 0, to: at('claude'), Card: RepoBeat},
  {from: at('claude'), to: at('if'), Card: Ready},
  {from: at('if'), to: at('builds'), Card: Interview},
  {from: at('builds'), to: at('and', 9.5), Card: Strategy},
  {from: at('and', 9.5), to: at('backed'), Card: Month},
  {from: at('backed'), to: at('so'), Card: Data},
  {from: at('so'), to: at('or', 18), Card: Post},
  {from: at('or', 18), to: at('this', 21), pop: false, Card: Review},
  {from: at('this', 21), to: at('comment'), Card: Recap},
  {from: at('comment'), to: DURATION, Card: Cta},
];

export const SFX: Sfx[] = [
  ...SCENES.filter((s) => s.pop !== false).map((s): Sfx => ['pop_light_3005', s.from, 0.3]),
  ['whoosh_air_1489', at('backed') - 0.12, 0.22],
  ['pop_dry_2356', at('impressions'), 0.4],
  ['pop_hard_click_2364', at('and', 22.5), 0.4],
];

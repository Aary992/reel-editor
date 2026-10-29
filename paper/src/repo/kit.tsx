// The repo look's cards: Claude Code terminal, white doc/browser card, GitHub repo card, checklist,
// counter over a field of documents, comment box. Every part takes the times it lands on.
import React from 'react';
import {C, MONO, SANS, SEAM, ease, pop, typed} from './style';

const BOX = {left: 60, top: 168, width: 960, height: 600};

// Mac window chrome: three dots and a path in the title bar.
const Chrome: React.FC<{title: string; dark?: boolean}> = ({title, dark}) => (
  <div
    style={{
      height: 50,
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '0 20px',
      borderBottom: `1.5px solid ${dark ? C.termLine : C.rule}`,
      background: dark ? C.termBar : '#FAFBFC',
      fontFamily: MONO,
      fontSize: 19,
      color: dark ? C.termDim : C.inkSoft,
    }}
  >
    {[0, 1, 2].map((i) => (
      <div key={i} style={{width: 12, height: 12, borderRadius: 6, background: dark ? '#3A4358' : '#D5D9E0'}} />
    ))}
    <span style={{marginLeft: 14}}>{title}</span>
  </div>
);

export const Window: React.FC<{title: string; dark?: boolean; box?: Partial<typeof BOX>; children: React.ReactNode}> = ({
  title,
  dark,
  box,
  children,
}) => (
  <div
    style={{
      position: 'absolute',
      ...BOX,
      ...box,
      borderRadius: 18,
      overflow: 'hidden',
      background: dark ? C.term : '#fff',
      boxShadow: '0 26px 60px rgba(20, 28, 48, 0.22), 0 4px 12px rgba(20, 28, 48, 0.08)',
      display: 'flex',
      flexDirection: 'column',
    }}
  >
    <Chrome title={title} dark={dark} />
    {children}
  </div>
);

// A terminal line. prompt: his typed message in a box (typed over `secs`). claude: orange bullet. tool: green
// bullet, "Name(arg)" with a dim "✓ read". sub: indented plain. row: indented blue label + text.
// badge: a coloured pill after the text.
export type Line = {
  at: number;
  kind: 'prompt' | 'claude' | 'tool' | 'sub' | 'row';
  text: string;
  label?: string;
  secs?: number;
  bold?: boolean;
  badge?: {text: string; color: string; at?: number};
};

const LineView: React.FC<{l: Line; t: number}> = ({l, t}) => {
  const k = ease(t, l.at, l.at + 0.18);
  const base: React.CSSProperties = {fontFamily: MONO, fontSize: 25, lineHeight: 1.5, color: C.termText, opacity: k};
  if (l.kind === 'prompt')
    return (
      <div style={{...base, opacity: 1, background: C.termBox, borderRadius: 8, padding: '8px 16px', margin: '4px 0 10px'}}>
        <span style={{color: C.termDim}}>&gt; </span>
        {typed(l.text, t, l.at, l.secs ?? 0.4)}
      </div>
    );
  const dot = l.kind === 'claude' ? C.orange : l.kind === 'tool' ? C.green : null;
  const badge = l.badge && t >= (l.badge.at ?? l.at) && (
    <span
      style={{
        marginLeft: 12,
        padding: '1px 12px 3px',
        borderRadius: 6,
        background: l.badge.color,
        color: '#10131A',
        fontFamily: SANS,
        fontWeight: 700,
        fontSize: 22,
        display: 'inline-block',
        transform: `scale(${0.7 + 0.3 * Math.min(1.15, pop(t, l.badge.at ?? l.at, 320))})`,
      }}
    >
      {l.badge.text}
    </span>
  );
  if (l.kind === 'row')
    return (
      <div style={{...base, display: 'flex', paddingLeft: 30}}>
        <span style={{color: C.termLabel, width: l.label && l.label.length > 7 ? 200 : 110, flexShrink: 0}}>{l.label}</span>
        <span>{l.text}</span>
      </div>
    );
  const m = l.kind === 'tool' ? /^(\w+)(\(.*\))(.*)$/.exec(l.text) : null;
  return (
    <div style={{...base, paddingLeft: dot ? 0 : 30, display: 'flex', alignItems: 'center'}}>
      {dot && <span style={{color: dot, width: 30, fontSize: 18, flexShrink: 0}}>●</span>}
      <span style={{fontWeight: l.bold ? 700 : 400}}>
        {m ? (
          <>
            <b>{m[1]}</b>
            {m[2]}
            <span style={{color: C.termDim}}>{m[3]}</span>
          </>
        ) : (
          l.text
        )}
      </span>
      {badge}
    </div>
  );
};

// Claude Code: lines appear on their words, newest at the bottom above the input box; old ones scroll off.
export const Terminal: React.FC<{t: number; lines: Line[]; title?: string}> = ({t, lines, title = 'claude · hattip-linkedin-os'}) => (
  <Window title={title} dark>
    <div style={{flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', padding: '0 26px'}}>
      {lines
        .filter((l) => t >= l.at)
        .map((l, i) => (
          <LineView key={i} l={l} t={t} />
        ))}
    </div>
    <div
      style={{
        margin: '12px 26px 24px',
        height: 74,
        border: `1.5px solid ${C.termLine}`,
        borderRadius: 10,
        display: 'flex',
        alignItems: 'center',
        padding: '0 18px',
        fontFamily: MONO,
        fontSize: 25,
        color: C.termDim,
      }}
    >
      &gt;
      <div style={{width: 3, height: 30, marginLeft: 12, background: '#4C7DFF', opacity: Math.floor(t * 2.2) % 2 ? 0.15 : 1}} />
    </div>
  </Window>
);

// GitHub repo card: name, Free pill, description, file list rows landing at `files[i][1]`.
export const RepoCard: React.FC<{t: number; name: string; desc: string; files: [string, number][]}> = ({t, name, desc, files}) => (
  <Window title={`github.com / ${name}`} box={{left: 90, width: 900, top: 190, height: 560}}>
    <div style={{padding: '34px 40px', fontFamily: SANS}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
        <span style={{color: C.link, fontWeight: 800, fontSize: 54, letterSpacing: '-0.03em'}}>{name}</span>
        <span style={{border: `2px solid ${C.rule}`, borderRadius: 20, padding: '2px 14px', fontSize: 20, fontWeight: 600, color: C.inkSoft}}>
          Free
        </span>
      </div>
      <div style={{fontSize: 27, color: C.ink, marginTop: 12, lineHeight: 1.35}}>{desc}</div>
      <div style={{marginTop: 24, border: `2px solid ${C.rule}`, borderRadius: 10}}>
        {files.map(([f, s], i) => (
          <div
            key={f}
            style={{
              fontFamily: MONO,
              fontSize: 22,
              color: C.ink,
              padding: '10px 18px',
              borderTop: i ? `2px solid ${C.rule}` : undefined,
              opacity: ease(t, s, s + 0.2),
              transform: `translateX(${(1 - ease(t, s, s + 0.25)) * -16}px)`,
            }}
          >
            <span style={{color: C.inkSoft}}>{f.includes('.md') ? '▪' : '▸'}</span> {f}
          </div>
        ))}
      </div>
    </div>
  </Window>
);

const Check: React.FC<{t: number; at: number; size?: number}> = ({t, at, size = 34}) => {
  const k = Math.min(1.15, pop(t, at, 320));
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        background: C.check,
        transform: `scale(${k})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexShrink: 0,
      }}
    >
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 20 20">
        <path d="M4 10.5l4 4 8-9" fill="none" stroke="#fff" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
};

// A doc with a title and rows: each row's text types in at its time, then its check pops.
export const Checklist: React.FC<{t: number; path: string; title: string; rows: [string, number][]; box?: Partial<typeof BOX>}> = ({
  t,
  path,
  title,
  rows,
  box,
}) => (
  <Window title={path} box={{left: 120, width: 840, top: 200, height: 540, ...box}}>
    <div style={{padding: '30px 44px', fontFamily: SANS}}>
      <div style={{fontWeight: 800, fontSize: 50, letterSpacing: '-0.03em', color: C.ink, paddingBottom: 14, borderBottom: `2px solid ${C.rule}`}}>
        {title}
      </div>
      {rows.map(([r, s], i) => (
        <div key={r} style={{display: 'flex', alignItems: 'center', gap: 20, height: 70, borderBottom: i < rows.length - 1 ? `2px solid ${C.rule}` : undefined}}>
          <div style={{width: 34, display: 'flex'}}>{t >= s + 0.22 && <Check t={t} at={s + 0.22} />}</div>
          <span style={{fontSize: 33, fontWeight: 600, color: C.ink}}>{typed(r, t, s, 0.22)}</span>
        </div>
      ))}
    </div>
  </Window>
);

// A big number counting up between `from` and `land` over a drifting field of small documents.
export const Counter: React.FC<{t: number; t0: number; from: number; land: number; value: number; label: string; plus?: boolean}> = ({
  t,
  t0,
  from,
  land,
  value,
  label,
  plus,
}) => {
  const docs = Array.from({length: 34}, (_, i) => {
    const r = (n: number) => ((Math.sin(i * 12.9898 + n * 78.233) * 43758.5453) % 1 + 1) % 1;
    return {x: 40 + r(1) * 980, y: 40 + r(2) * 740, at: t0 + r(3) * 0.9, s: 0.75 + r(4) * 0.45, v: 14 + r(5) * 22};
  }).filter((d) => !(d.x > 230 && d.x < 850 && d.y > 260 && d.y < 600));
  const k = ease(t, from, land);
  const n = Math.round(value * (1 - Math.pow(1 - k, 2.2)));
  return (
    <div style={{position: 'absolute', left: 0, top: 0, width: 1080, height: SEAM, overflow: 'hidden'}}>
      {docs.map((d, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            left: d.x,
            top: d.y - (t - t0) * d.v,
            width: 50 * d.s,
            height: 64 * d.s,
            background: '#fff',
            borderRadius: 5,
            boxShadow: '0 4px 10px rgba(20,28,48,0.10)',
            opacity: ease(t, d.at, d.at + 0.3) * 0.9,
            padding: 8 * d.s,
          }}
        >
          {[0.9, 0.7, 0.8, 0.5].map((w, j) => (
            <div key={j} style={{height: 4 * d.s, width: `${w * 100}%`, background: '#D9DDE4', borderRadius: 2, marginTop: j ? 6 * d.s : 0}} />
          ))}
        </div>
      ))}
      <div
        style={{
          position: 'absolute',
          left: '50%',
          top: 430,
          transform: `translate(-50%, -50%) scale(${0.9 + 0.1 * Math.min(1.1, pop(t, t0 + 0.15))})`,
          background: '#fff',
          borderRadius: 26,
          padding: '34px 56px 30px',
          boxShadow: '0 26px 60px rgba(20, 28, 48, 0.2)',
          textAlign: 'center',
          fontFamily: SANS,
          whiteSpace: 'nowrap',
        }}
      >
        <div style={{fontWeight: 800, fontSize: 112, letterSpacing: '-0.045em', color: C.ink, lineHeight: 1}}>
          {n.toLocaleString('en-US')}
          {plus && t >= land && (
            <span style={{color: C.blue, display: 'inline-block', transform: `scale(${Math.min(1.2, pop(t, land, 320))})`}}>+</span>
          )}
        </div>
        <div style={{fontWeight: 600, fontSize: 32, color: C.inkSoft, marginTop: 10}}>{label}</div>
      </div>
    </div>
  );
};

// Comment box: avatar, "Add a comment..." pill that types `word` at `typeAt`, send button lights at `sendAt`.
export const CommentBox: React.FC<{t: number; word: string; typeAt: number; sendAt: number}> = ({t, word, typeAt, sendAt}) => {
  const txt = typed(word, t, typeAt, 0.3);
  const sent = t >= sendAt;
  const k = Math.min(1.15, pop(t, sendAt, 320));
  return (
    <div
      style={{
        position: 'absolute',
        left: 90,
        width: 900,
        top: 300,
        background: '#fff',
        borderRadius: 22,
        boxShadow: '0 26px 60px rgba(20, 28, 48, 0.2)',
        padding: '30px 34px',
        display: 'flex',
        alignItems: 'center',
        gap: 22,
        fontFamily: SANS,
      }}
    >
      <div style={{width: 76, height: 76, borderRadius: 38, background: 'linear-gradient(135deg, #C9D3E6, #9AA8C4)', flexShrink: 0}} />
      <div
        style={{
          flex: 1,
          height: 84,
          border: `2px solid ${txt ? C.blue : C.rule}`,
          borderRadius: 42,
          display: 'flex',
          alignItems: 'center',
          padding: '0 30px',
          fontSize: 36,
          color: txt ? C.ink : '#8A92A3',
          fontWeight: txt ? 700 : 500,
        }}
      >
        {txt || 'Add a comment...'}
        {txt && !sent && <div style={{width: 3, height: 38, marginLeft: 4, background: C.blue, opacity: Math.floor(t * 2.2) % 2 ? 0.2 : 1}} />}
      </div>
      <div
        style={{
          width: 84,
          height: 84,
          borderRadius: 42,
          background: sent ? C.blue : '#E3E7EE',
          transform: `scale(${sent ? 0.85 + 0.15 * k : 1})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <svg width={38} height={38} viewBox="0 0 24 24">
          <path d="M5 12h13M12 5l7 7-7 7" fill="none" stroke={sent ? '#fff' : '#8A92A3'} strokeWidth={2.8} strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </div>
  );
};

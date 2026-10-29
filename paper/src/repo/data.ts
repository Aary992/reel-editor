// The reel being edited: written by `repo.py prep` into reel.json (clips with his face box, words).
import reel from './reel.json';

// One beat: the top-panel card from `from` to `to` seconds. `pop` animates the card in (off when the
// previous beat is the same window, e.g. one terminal clearing for the next prompt).
export type Scene = {from: number; to: number; pop?: boolean; Card: React.FC<{t: number; t0: number}>};
// [sound effect file in public/repo/sfx without .wav, second, volume 0..1]
export type Sfx = [string, number, number];

type Word = {w: string; s: number; e: number};
export type Clip = {t0: number; hair: number; chin: number; cx: number};

export const NAME: string = (reel as any).name;
export const FPS: number = (reel as any).fps;
export const DURATION: number = (reel as any).duration;
export const TOTAL_FRAMES = Math.round(DURATION * FPS);
export const WORDS: Word[] = (reel as any).words;
export const CLIPS: Clip[] = (reel as any).clips;

export const clipAt = (t: number) => {
  let i = 0;
  while (i + 1 < CLIPS.length && t >= CLIPS[i + 1].t0 - 1e-3) i++;
  return {i, ...CLIPS[i]};
};

export const clean = (w: string) => w.trim().toLowerCase().replace(/[.,!?]/g, '');

// Time of a spoken word, so every graphic lands on the word (first match at or after `after` seconds).
export const at = (word: string, after = 0) => {
  const hit = WORDS.find((x) => x.s >= after - 1e-3 && clean(x.w) === word.toLowerCase());
  if (!hit) throw new Error(`word not found: ${word} after ${after}`);
  return hit.s;
};

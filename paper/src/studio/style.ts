// The studio look, sampled from his two reference reels (Downloads/Video-27200.mp4, Video-3661.mp4).
import {Easing, interpolate, spring} from 'remotion';
import {loadFont as loadSans} from '@remotion/google-fonts/DMSans';
import {loadFont as loadSerif} from '@remotion/google-fonts/SourceSerif4';
import {FPS} from './data';

export const {fontFamily: SANS} = loadSans('normal', {weights: ['400', '500', '600', '700'], subsets: ['latin']});
export const {fontFamily: SERIF} = loadSerif('normal', {weights: ['400', '600'], subsets: ['latin']});

export const C = {
  plane: '#EDEAEE',        // the lit grey backdrop (centre of his frames: #E8E5E9 under the vignette)
  rule: 'rgba(48, 44, 52, 0.075)',
  ink: '#151417',
  inkSoft: '#6B6770',
  orange: '#D97757',       // Claude's orange: the mark, send button, highlights
  peach: '#F6DCC8',
  hl: 'rgba(236, 150, 104, 0.42)',
  card: '#FFFFFF',
  cardLine: '#E3DFD9',
  claudeText: '#2E2C29',
  claudeMute: '#8E8A82',
  bubble: '#EFEBE3',
  dark: '#2A282C',
};

export const clamp = (x: number, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const mix = (a: number, b: number, k: number) => a + (b - a) * k;

// 0 before t0, springs to 1 (small overshoot) after.
export const pop = (t: number, t0: number, stiff = 210) =>
  t < t0 ? 0 : spring({frame: (t - t0) * FPS, fps: FPS, config: {damping: 14, stiffness: stiff, mass: 0.6}});

// 0..1 between t0 and t1, ease-out (arrivals) or in-out (camera moves).
export const ease = (t: number, t0: number, t1: number) =>
  interpolate(t, [t0, t1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
export const easeIO = (t: number, t0: number, t1: number) =>
  interpolate(t, [t0, t1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.65, 0, 0.3, 1)});

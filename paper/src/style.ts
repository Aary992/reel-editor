// His look, sampled from the reference frames (References/Video-13947.mp4).
import {Easing, interpolate, spring} from 'remotion';
import {loadFont} from '@remotion/google-fonts/InterTight';
import {FPS} from './data';

export const {fontFamily: FONT} = loadFont('normal', {weights: ['600', '700', '800', '900'], subsets: ['latin']});

export const C = {
  paper: '#DFD6C4',
  grid: 'rgba(120, 100, 72, 0.11)',
  terracotta: '#CB603E',
  ink: '#1C1814',
  inkSoft: '#5A5047',
  line: '#4B423A',
  folder: '#76CDF2',
  folderDeep: '#4FAEE6',
  folderLight: '#A9E0F8',
  card: '#FFFFFF',
  cardLine: '#E7E3DC',
};

// 0 before t0, springs to 1 (with his small overshoot) after.
export const pop = (t: number, t0: number, stiff = 200) =>
  t < t0 ? 0 : spring({frame: (t - t0) * FPS, fps: FPS, config: {damping: 13, stiffness: stiff, mass: 0.6}});

// 0..1 eased progress between t0 and t1.
export const ease = (t: number, t0: number, t1: number) =>
  interpolate(t, [t0, t1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});

export const mix = (a: number, b: number, k: number) => a + (b - a) * k;

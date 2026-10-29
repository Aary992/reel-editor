// The repo look, sampled from the reference frames (Downloads/Video-16746.mp4).
import {Easing, interpolate, spring} from 'remotion';
import {loadFont as inter} from '@remotion/google-fonts/Inter';
import {loadFont as mono} from '@remotion/google-fonts/JetBrainsMono';
import {loadFont as pixel} from '@remotion/google-fonts/Silkscreen';
import {FPS} from './data';

export const {fontFamily: SANS} = inter('normal', {weights: ['500', '600', '700', '800'], subsets: ['latin']});
export const {fontFamily: MONO} = mono('normal', {weights: ['400', '500', '700'], subsets: ['latin']});
export const {fontFamily: PIXEL} = pixel('normal', {weights: ['400', '700'], subsets: ['latin']});

export const SEAM = 840; // the top panel's bottom edge, 43.75% down like the reference

export const C = {
  panel: '#ECEEF1',
  dot: 'rgba(60, 72, 96, 0.09)',
  blue: '#1F49FF',
  lime: '#E2FF3B',
  term: '#0E1424',
  termBar: '#131A2C',
  termBox: '#1A2236',
  termLine: '#262F45',
  termText: '#E4E8F1',
  termDim: '#7C869B',
  termLabel: '#79A0F5',
  orange: '#E5794B',
  green: '#3FB950',
  amber: '#F2A62A',
  ink: '#14171F',
  inkSoft: '#5B6375',
  rule: '#E5E8EE',
  link: '#2457E6',
  check: '#1F9D55',
};

export const pop = (t: number, t0: number, stiff = 220) =>
  t < t0 ? 0 : spring({frame: (t - t0) * FPS, fps: FPS, config: {damping: 14, stiffness: stiff, mass: 0.6}});

export const ease = (t: number, t0: number, t1: number) =>
  interpolate(t, [t0, t1], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});

// Text typed out between t0 and t0 + secs.
export const typed = (s: string, t: number, t0: number, secs: number) =>
  t < t0 ? '' : s.slice(0, Math.ceil(s.length * Math.min(1, (t - t0) / Math.max(secs, 0.01))));

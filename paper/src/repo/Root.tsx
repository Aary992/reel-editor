import React from 'react';
import {Composition} from 'remotion';
import {Repo} from './Repo';
import {FPS, TOTAL_FRAMES} from './data';

export const RepoRoot: React.FC = () => (
  <Composition id="Repo" component={Repo} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1080} height={1920} />
);

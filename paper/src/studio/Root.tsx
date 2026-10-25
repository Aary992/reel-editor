import React from 'react';
import {Composition} from 'remotion';
import {Studio} from './Studio';
import {FPS, TOTAL_FRAMES} from './data';

export const StudioRoot: React.FC = () => (
  <Composition id="Studio" component={Studio} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1080} height={1920} />
);

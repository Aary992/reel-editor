// The studio look's own entry point, so a broken or foreign paper beats.tsx never touches it.
import {registerRoot} from 'remotion';
import {StudioRoot} from './Root';

registerRoot(StudioRoot);

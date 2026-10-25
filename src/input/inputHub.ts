/** รวม input ทุกแบบเข้า InputSink เดียว · คืนตัว poll (จอย) กับตัวถอด */
import { bindHeldKeys, bindKeyboard } from './keyboard';
import { createPadPoller } from './gamepad';
import { bindPointer } from './pointer';
import type { InputSink } from './types';

export interface InputHub {
  poll(padDeadzone: number): void;
  dispose(): void;
}

export function createInputHub(canvas: HTMLCanvasElement, sink: InputSink): InputHub {
  const offKeys = bindKeyboard(sink);
  const offPointer = bindPointer(canvas, sink);
  const pad = createPadPoller(sink);
  const held = bindHeldKeys();
  return {
    poll(deadzone) {
      const [px, py, prun] = pad.poll(deadzone);
      const [kx, ky, krun] = held.axis();
      sink.move(px + kx, py + ky, prun || krun);
    },
    dispose() {
      held.dispose();
      offKeys();
      offPointer();
    },
  };
}

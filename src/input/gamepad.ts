/** จอย (Gamepad API) : ต้อง poll ทุกเฟรม · ปุ่มสั่งงานจับขอบกด (กดครั้งเดียวต่อหนึ่งการกด) · แกนส่งต่อทุกเฟรม */
import { applyDeadzone } from '../logic/axis';
import { PAD_MAP } from './inputMap';
import type { InputSink } from './types';

export interface PadPoller {
  /** คืน [ขวา, หน้า, วิ่ง] ของคันโยกซ้าย (ไม่มีจอย = ศูนย์) */
  poll(deadzone: number): [number, number, boolean];
}

function firstPad(): Gamepad | null {
  for (const pad of navigator.getGamepads()) if (pad && pad.connected) return pad;
  return null;
}

export function createPadPoller(sink: InputSink): PadPoller {
  const wasDown = new Map<number, boolean>();

  const pollButtons = (pad: Gamepad): void => {
    for (const [idx, action] of Object.entries(PAD_MAP.buttons)) {
      const i = Number(idx);
      const down = pad.buttons[i]?.pressed ?? false;
      if (down && !wasDown.get(i)) sink.action(action);
      wasDown.set(i, down);
    }
  };

  return {
    poll(deadzone) {
      const pad = firstPad();
      if (!pad) return [0, 0, false];
      pollButtons(pad);
      sink.padRotate(applyDeadzone(pad.axes[PAD_MAP.stickX] ?? 0, deadzone), applyDeadzone(pad.axes[PAD_MAP.stickY] ?? 0, deadzone));
      const zoomIn = pad.buttons[PAD_MAP.zoomInButton]?.value ?? 0;
      const zoomOut = pad.buttons[PAD_MAP.zoomOutButton]?.value ?? 0;
      sink.padZoom(applyDeadzone(zoomIn - zoomOut, deadzone));
      const mx = applyDeadzone(pad.axes[PAD_MAP.moveX] ?? 0, deadzone);
      const my = -applyDeadzone(pad.axes[PAD_MAP.moveY] ?? 0, deadzone);
      return [mx, my, pad.buttons[PAD_MAP.runButton]?.pressed ?? false];
    },
  };
}

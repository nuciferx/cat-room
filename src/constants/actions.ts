/** การกระทำที่ input map กลางแปลงปุ่มให้ (action → ปุ่มอยู่ใน src/input/inputMap.ts) */
export const ACTION = {
  prevClip: 'prevClip',
  nextClip: 'nextClip',
  nextFace: 'nextFace',
  nextView: 'nextView',
  togglePlay: 'togglePlay',
  toggleGrid: 'toggleGrid',
  togglePanel: 'togglePanel',
  toggleHelp: 'toggleHelp',
  resetCamera: 'resetCamera',
} as const;

export type Action = (typeof ACTION)[keyof typeof ACTION];

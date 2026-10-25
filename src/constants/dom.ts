/** id และ class ของ DOM ที่ cat.html กับโค้ด UI ใช้ร่วมกัน */

export const DOM_ID = {
  canvas: 'stage',
  clipBar: 'clip-bar',
  faceBar: 'face-bar',
  viewBar: 'view-bar',
  current: 'clip-current',
  help: 'help',
  banner: 'banner',
  helpToggle: 'help-toggle',
  bar: 'bar',
  tune: 'tune-host',
} as const;

export const CSS = {
  clipButton: 'clip-btn',
  active: 'is-active',
  hidden: 'is-hidden',
  paused: 'is-paused',
  helpRow: 'help-row',
  compact: 'is-compact',
} as const;

/** แผงจูน F1 ด้วย lil-gui : สร้าง slider/ช่องสี อัตโนมัติจากทุกกลุ่มใน config (value/min/max/step)
 *  แก้ค่าในสำเนา config ที่แอปถือ แล้วเรียก onChange ให้แอปอัปเดตฉาก · ปุ่มคัดลอกส่งค่าทั้งหมดเป็น JSON */
import GUI from 'lil-gui';
import { isNumParam, serializeConfig, type CatConfig, type ColorParam, type NumParam } from '../data/config';
import type { Translate } from '../data/locale';

export interface TunePanel {
  setOpen(open: boolean): void;
}

export interface TuneHooks {
  onChange(): void;
  notify(text: string): void;
}

function addParam(folder: GUI, param: NumParam | ColorParam, label: string, onChange: () => void): void {
  const ctrl = isNumParam(param)
    ? folder.add(param, 'value', param.min, param.max, param.step)
    : folder.addColor(param, 'value');
  ctrl.name(label).onChange(onChange);
}

function addCopyButton(gui: GUI, cfg: CatConfig, t: Translate, notify: (text: string) => void): void {
  const actions = {
    copy: () => {
      navigator.clipboard.writeText(serializeConfig(cfg)).then(
        () => notify(t('tune.copied')),
        () => notify(t('tune.copyFailed')),
      );
    },
  };
  gui.add(actions, 'copy').name(t('tune.copy'));
}

export function createTunePanel(host: HTMLElement, cfg: CatConfig, t: Translate, hooks: TuneHooks): TunePanel {
  const gui = new GUI({ container: host, title: t('tune.title') });
  for (const [group, params] of Object.entries(cfg)) {
    const folder = gui.addFolder(t(`tune.group.${group}`)).close();
    for (const [key, param] of Object.entries(params as Record<string, NumParam | ColorParam>)) {
      addParam(folder, param, t(`tune.param.${group}.${key}`), hooks.onChange);
    }
  }
  addCopyButton(gui, cfg, t, hooks.notify);
  gui.hide();
  return { setOpen: (open) => gui.show(open) };
}

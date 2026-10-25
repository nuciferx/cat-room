/** ฉากรวม : renderer + ฟ้า + แสง + พื้น + env map เบา ๆ · ?q=low → pixelRatio ต่ำ ไม่มีเงา ไม่มี env
 *  แมวสูง 0.4 ม. : ค่า near/far กล้องและกรอบเงาอยู่ใน config ไม่ใช่ขนาดคน */
import {
  ACESFilmicToneMapping, PMREMGenerator, PCFShadowMap, Scene, WebGLRenderer, type Camera, type Texture,
} from 'three';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import type { CatConfig } from '../data/config';
import { createFloor, type Floor } from './floor';
import { createLighting, type Lighting } from './lighting';
import { makeSkyTexture } from './sky';

export interface Stage {
  scene: Scene;
  floor: Floor;
  apply(cfg: CatConfig): void;
  resize(width: number, height: number, cfg: CatConfig): void;
  render(camera: Camera): void;
}

function buildEnvironment(renderer: WebGLRenderer): Texture {
  const pmrem = new PMREMGenerator(renderer);
  const env = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
  pmrem.dispose();
  return env;
}

export function createStage(canvas: HTMLCanvasElement, low: boolean, gridOn: boolean): Stage {
  const renderer = new WebGLRenderer({ canvas, antialias: !low });
  renderer.shadowMap.enabled = !low;
  renderer.shadowMap.type = PCFShadowMap;
  renderer.toneMapping = ACESFilmicToneMapping;

  const scene = new Scene();
  if (!low) scene.environment = buildEnvironment(renderer);
  const lighting: Lighting = createLighting(scene, !low);
  const floor = createFloor(scene, gridOn);
  let skyKey = '';

  const applySky = (cfg: CatConfig): void => {
    const key = `${cfg.sky.topColor.value}/${cfg.sky.horizonColor.value}`;
    if (key === skyKey) return;
    skyKey = key;
    (scene.background as Texture | null)?.dispose();
    scene.background = makeSkyTexture(cfg.sky.topColor.value, cfg.sky.horizonColor.value);
  };

  return {
    scene,
    floor,
    apply(cfg) {
      renderer.toneMappingExposure = cfg.light.exposure.value;
      scene.environmentIntensity = cfg.light.envIntensity.value;
      applySky(cfg);
      lighting.apply(cfg);
      floor.apply(cfg);
    },
    resize(width, height, cfg) {
      const ratio = low ? cfg.render.lowPixelRatio.value : Math.min(window.devicePixelRatio, cfg.render.pixelRatioMax.value);
      renderer.setPixelRatio(ratio);
      renderer.setSize(width, height, false);
    },
    render(camera) {
      renderer.render(scene, camera);
    },
  };
}

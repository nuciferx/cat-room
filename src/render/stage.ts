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
  /** ขนาดภาพสูงสุดต่อด้านที่การ์ดจอรองรับ (พิกเซล) */
  maxTextureSize: number;
  /** compact = จอสัมผัส/จอแคบ : pixelRatio และแผนที่เงาเบาลง */
  apply(cfg: CatConfig, compact: boolean): void;
  resize(width: number, height: number, cfg: CatConfig, compact: boolean): void;
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
    maxTextureSize: renderer.capabilities.maxTextureSize,
    apply(cfg, compact) {
      renderer.toneMappingExposure = cfg.light.exposure.value;
      scene.environmentIntensity = cfg.light.envIntensity.value;
      applySky(cfg);
      lighting.apply(cfg, compact);
      floor.apply(cfg);
    },
    resize(width, height, cfg, compact) {
      const maxRatio = compact ? Math.min(cfg.render.pixelRatioMax.value, cfg.render.touchPixelRatioMax.value) : cfg.render.pixelRatioMax.value;
      const ratio = low ? cfg.render.lowPixelRatio.value : Math.min(window.devicePixelRatio, maxRatio);
      renderer.setPixelRatio(ratio);
      renderer.setSize(width, height, false);
    },
    render(camera) {
      renderer.render(scene, camera);
    },
  };
}

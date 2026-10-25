/** แสง : hemisphere + directional (มีเงา) · ปรับค่าสดจาก config ด้วย apply() ทุกครั้งที่แผง F1 ขยับ
 *  จุดที่ไม่ชัด : เปลี่ยน mapSize ต้องทิ้ง shadow map เดิมให้ three สร้างใหม่ */
import { Color, DirectionalLight, HemisphereLight, type Scene } from 'three';
import type { CatConfig } from '../data/config';
import { sunDirection } from '../logic/orbit';

export interface Lighting {
  /** compact = จอสัมผัส/จอแคบ : ลดขนาดแผนที่เงา */
  apply(cfg: CatConfig, compact: boolean): void;
}

export function createLighting(scene: Scene, shadowsOn: boolean): Lighting {
  const hemi = new HemisphereLight();
  const sun = new DirectionalLight();
  sun.castShadow = shadowsOn;
  scene.add(hemi, sun, sun.target);

  const applyShadow = (cfg: CatConfig['shadow'], mapSize: number): void => {
    if (sun.shadow.mapSize.x !== mapSize) {
      sun.shadow.map?.dispose();
      sun.shadow.map = null;
      sun.shadow.mapSize.set(mapSize, mapSize);
    }
    const half = cfg.frustumHalfM.value;
    const cam = sun.shadow.camera;
    cam.left = -half;
    cam.right = half;
    cam.top = half;
    cam.bottom = -half;
    cam.near = cfg.near.value;
    cam.far = cfg.far.value;
    cam.updateProjectionMatrix();
    sun.shadow.bias = cfg.bias.value;
    sun.shadow.normalBias = cfg.normalBias.value;
    sun.shadow.radius = cfg.radius.value;
  };

  return {
    apply(cfg, compact) {
      const l = cfg.light;
      hemi.intensity = l.hemiIntensity.value;
      hemi.color = new Color(l.hemiSkyColor.value);
      hemi.groundColor = new Color(l.hemiGroundColor.value);
      sun.intensity = l.sunIntensity.value;
      sun.color = new Color(l.sunColor.value);
      const dir = sunDirection(l.sunAzimuthDeg.value, l.sunElevationDeg.value);
      const dist = l.sunDistanceM.value;
      sun.position.set(dir.x * dist, dir.y * dist, dir.z * dist);
      const size = compact ? Math.min(cfg.shadow.mapSize.value, cfg.render.touchShadowMapSize.value) : cfg.shadow.mapSize.value;
      applyShadow(cfg.shadow, size);
    },
  };
}

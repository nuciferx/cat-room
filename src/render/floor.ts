/** พื้นเรียบ + เส้นตาราง (ช่องละ 10 ซม. ตาม config) เปิด/ปิดได้ · สร้างตารางใหม่เฉพาะตอนขนาด/ช่องเปลี่ยน */
import { Color, GridHelper, LineBasicMaterial, Mesh, MeshStandardMaterial, PlaneGeometry, type Scene } from 'three';
import type { CatConfig } from '../data/config';

export interface Floor {
  apply(cfg: CatConfig): void;
  setGridVisible(on: boolean): void;
}

export function createFloor(scene: Scene, gridOn: boolean): Floor {
  const material = new MeshStandardMaterial();
  const plane = new Mesh(new PlaneGeometry(1, 1), material);
  plane.rotation.x = -Math.PI / 2;
  plane.receiveShadow = true;
  scene.add(plane);

  let grid: GridHelper | null = null;
  let gridKey = '';
  let gridVisible = gridOn;

  const rebuildGrid = (g: CatConfig['grid']): void => {
    const key = `${g.sizeM.value}/${g.cellM.value}/${g.color.value}`;
    if (key === gridKey) return;
    gridKey = key;
    if (grid) {
      scene.remove(grid);
      grid.geometry.dispose();
      (grid.material as LineBasicMaterial).dispose();
    }
    const color = new Color(g.color.value);
    grid = new GridHelper(g.sizeM.value, Math.max(1, Math.round(g.sizeM.value / g.cellM.value)), color, color);
    (grid.material as LineBasicMaterial).transparent = true;
    scene.add(grid);
  };

  return {
    apply(cfg) {
      material.color = new Color(cfg.floor.color.value);
      material.roughness = cfg.floor.roughness.value;
      plane.scale.setScalar(cfg.floor.sizeM.value);
      rebuildGrid(cfg.grid);
      grid!.position.y = cfg.grid.liftM.value;
      (grid!.material as LineBasicMaterial).opacity = cfg.grid.opacity.value;
      grid!.visible = gridVisible;
    },
    setGridVisible(on) {
      gridVisible = on;
      if (grid) grid.visible = on;
    },
  };
}

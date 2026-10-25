/** โหลด cat.glb ด้วย GLTFLoader · ล้มเหลวให้โยน error (ผู้เรียกตัดสินใจใช้แคปซูลแทน) */
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';

export function loadCatGltf(url: string): Promise<GLTF> {
  return new GLTFLoader().loadAsync(url);
}

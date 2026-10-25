// ตรวจ glb ของสัตว์สี่ขา Meshy (node ล้วน ไม่พึ่ง Blender) : คลิปครบตามไฟล์ค่า · งบสามเหลี่ยม/ไฟล์/ภาพ
// · index ไม่เกินจำนวนจุด · JOINTS ไม่เกินจำนวนกระดูกของ skin · WEIGHTS รวม 1 · ไม่มี NaN ในทุก accessor float
// รัน : node tools/blender/quad_meshy_check.mjs boar dog   (ผล = บรรทัด JSON ต่อตัว · exit 1 ถ้ามีข้อไม่ผ่าน)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..', '..');
const COMP = { 5120: Int8Array, 5121: Uint8Array, 5122: Int16Array, 5123: Uint16Array, 5125: Uint32Array, 5126: Float32Array };
const NCOMP = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };

function readGlb(file) {
  const b = fs.readFileSync(file);
  const jsonLen = b.readUInt32LE(12);
  const gltf = JSON.parse(b.subarray(20, 20 + jsonLen).toString('utf8'));
  const binStart = 20 + jsonLen + 8;
  return { gltf, bin: b.subarray(binStart), bytes: b.length };
}

function accessor(glb, i) {
  const a = glb.gltf.accessors[i];
  const v = glb.gltf.bufferViews[a.bufferView];
  const T = COMP[a.componentType];
  const n = NCOMP[a.type];
  const stride = v.byteStride || n * T.BYTES_PER_ELEMENT;
  const out = new Float64Array(a.count * n);
  const dv = new DataView(glb.bin.buffer, glb.bin.byteOffset + (v.byteOffset || 0) + (a.byteOffset || 0));
  const get = { 5120: 'getInt8', 5121: 'getUint8', 5122: 'getInt16', 5123: 'getUint16', 5125: 'getUint32', 5126: 'getFloat32' }[a.componentType];
  for (let r = 0; r < a.count; r++) {
    for (let c = 0; c < n; c++) out[r * n + c] = dv[get](r * stride + c * T.BYTES_PER_ELEMENT, true);
  }
  const scale = a.normalized ? { 5121: 255, 5123: 65535 }[a.componentType] || 1 : 1;
  return { data: scale === 1 ? out : out.map((x) => x / scale), n, count: a.count };
}

function jpegSize(buf) {
  for (let i = 2; i < buf.length - 9;) {
    if (buf[i] !== 0xff) return null;
    const m = buf[i + 1];
    if (m >= 0xc0 && m <= 0xc2) return [buf.readUInt16BE(i + 7), buf.readUInt16BE(i + 5)];
    i += 2 + buf.readUInt16BE(i + 2);
  }
  return null;
}

function imageSizes(glb) {
  return (glb.gltf.images || []).map((im) => {
    const v = glb.gltf.bufferViews[im.bufferView];
    const buf = glb.bin.subarray(v.byteOffset || 0, (v.byteOffset || 0) + v.byteLength);
    return im.mimeType === 'image/png' ? [buf.readUInt32BE(16), buf.readUInt32BE(20)] : jpegSize(buf);
  });
}

function checkPrimitive(glb, prim, joints, fail) {
  const pos = accessor(glb, prim.attributes.POSITION);
  const idx = accessor(glb, prim.indices).data;
  if (idx.some((k) => k >= pos.count)) fail.push('index เกินจำนวนจุด');
  const j = accessor(glb, prim.attributes.JOINTS_0).data;
  if (j.some((k) => k >= joints)) fail.push('JOINTS เกินจำนวนกระดูก');
  const w = accessor(glb, prim.attributes.WEIGHTS_0);
  let worst = 0;
  for (let r = 0; r < w.count; r++) {
    let s = 0;
    for (let c = 0; c < 4; c++) s += w.data[r * 4 + c];
    worst = Math.max(worst, Math.abs(s - 1));
  }
  if (worst > 1e-3) fail.push('น้ำหนักรวมไม่เท่า 1 (คลาด ' + worst.toFixed(4) + ')');
  return { tris: idx.length / 3, verts: pos.count, weightSumErr: Number(worst.toExponential(2)) };
}

function nanCount(glb) {
  let bad = 0;
  glb.gltf.accessors.forEach((a, i) => {
    if (a.componentType === 5126 && a.bufferView !== undefined) bad += accessor(glb, i).data.filter((x) => !Number.isFinite(x)).length;
  });
  return bad;
}

function check(key) {
  const cfg = JSON.parse(fs.readFileSync(path.join(HERE, `quad_meshy_${key}.json`), 'utf8'));
  const glb = readGlb(path.join(ROOT, cfg.out));
  const g = glb.gltf;
  const fail = [];
  const joints = g.skins[0].joints.length;
  const prims = g.meshes.flatMap((m) => m.primitives).map((p) => checkPrimitive(glb, p, joints, fail));
  const tris = prims.reduce((s, p) => s + p.tris, 0);
  const clips = g.animations.map((a) => a.name);
  const missing = cfg.clips.order.filter((c) => !clips.includes(c));
  const nan = nanCount(glb);
  const kb = glb.bytes / 1024;
  const images = imageSizes(glb);
  if (missing.length) fail.push('ขาดคลิป ' + missing.join(' '));
  if (nan) fail.push('มี NaN/Inf ' + nan + ' ค่า');
  if (tris > cfg.budget.tris) fail.push('สามเหลี่ยมเกินงบ');
  if (kb > cfg.budget.fileKB) fail.push('ไฟล์เกินงบ');
  if (images.some((s) => !s || Math.max(...s) > cfg.budget.texPx)) fail.push('ภาพเกิน ' + cfg.budget.texPx);
  const nodes = g.nodes.map((n) => n.name);
  const mat = g.materials.map((m) => ({ name: m.name, metallic: m.pbrMetallicRoughness.metallicFactor ?? 1,
    roughness: m.pbrMetallicRoughness.roughnessFactor ?? 1, normalMap: Boolean(m.normalTexture), doubleSided: Boolean(m.doubleSided) }));
  return { animal: key, ok: fail.length === 0, fail, tris, KB: Number(kb.toFixed(1)), joints, prims, images, clips: clips.length,
    clipNames: clips, extraClips: clips.filter((c) => !cfg.clips.order.includes(c)), mouthItem: nodes.includes('mouth_item'), materials: mat };
}

const keys = process.argv.slice(2);
let allOk = true;
for (const key of keys.length ? keys : ['boar']) {
  const r = check(key);
  allOk &&= r.ok;
  console.log(JSON.stringify(r));
}
process.exit(allOk ? 0 : 1);

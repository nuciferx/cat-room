"""คณิตท่าของนก (numpy ล้วน) : หมุนรอบแกนนก · FK แบบเดลตาในกรอบโลก · IK ขาสองท่อน (ข้อเท้าพับไปหลังแบบนก)
กรอบนก = แบบ glTF (x ซ้าย y ขึ้น z หน้า) · มุมก้ม (pitch) + = หัวก้มลง / ของที่ชี้ไปหลังเงยขึ้น
ท่าของกระดูก b = การแปลง x ↦ D_b (x - หัวกระดูกตอนพัก) + p_b (D = การหมุนสะสมในกรอบโลก)"""
import math

import numpy as np

EPS = 1e-9
SIDES = ('L', 'R')


def rx(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def axis_angle(axis, angle):
    k = np.asarray(axis, dtype=float)
    k = k / max(np.linalg.norm(k), EPS)
    kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(angle) * kx + (1 - math.cos(angle)) * kx @ kx


def rot_between(a, b):
    """การหมุนน้อยที่สุดที่พาเวกเตอร์ a ไปทิศ b"""
    a, b = a / np.linalg.norm(a), b / np.linalg.norm(b)
    c = float(np.clip(np.dot(a, b), -1, 1))
    axis = np.cross(a, b)
    if np.linalg.norm(axis) < 1e-8:
        return np.eye(3)
    return axis_angle(axis, math.acos(c))


def partial(r, f):
    """ทางผ่านจาก I ไปหา r เป็นสัดส่วน f (slerp ของเมทริกซ์หมุน)"""
    ang = math.acos(float(np.clip((np.trace(r) - 1) / 2, -1, 1)))
    if ang < 1e-8:
        return np.eye(3)
    axis = np.array([r[2, 1] - r[1, 2], r[0, 2] - r[2, 0], r[1, 0] - r[0, 1]])
    return axis_angle(axis, ang * f)


class Pose:
    """off = เลื่อน root · local = หมุนเทียบแม่ · absolute = หมุนสะสมกำหนดตรง · feet = {ข้าง: (เป้าข้อเท้า, หมุนเท้า)}"""

    def __init__(self):
        self.off = np.zeros(3)
        self.local, self.absolute, self.feet = {}, {}, {}


class Rig:
    """โครงกระดูกตอนพัก (กรอบนก) : order = แม่มาก่อนลูก"""

    def __init__(self, bones):
        self.order = [b[0] for b in bones]
        self.parent = {b[0]: b[1] for b in bones}
        self.head = {b[0]: np.asarray(b[2], dtype=float) for b in bones}
        self.tail = {b[0]: np.asarray(b[3], dtype=float) for b in bones}
        self.dir = {n: (self.tail[n] - self.head[n]) / np.linalg.norm(self.tail[n] - self.head[n]) for n in self.order}
        self.len = {n: float(np.linalg.norm(self.tail[n] - self.head[n])) for n in self.order}

    def ankle(self, side):
        return self.head['foot_' + side]


def knee(hip, foot, l1, l2, pole):
    """ข้อพับ (ข้อเท้านก) : ห่างสะโพก l1 ห่างเท้า l2 พับไปทาง pole"""
    d_vec = foot - hip
    d = float(np.clip(np.linalg.norm(d_vec), abs(l1 - l2) + 1e-5, l1 + l2 - 1e-5))
    u = d_vec / max(np.linalg.norm(d_vec), EPS)
    w = pole - np.dot(pole, u) * u
    w = w / max(np.linalg.norm(w), EPS)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    return hip + u * a + w * math.sqrt(max(l1 * l1 - a * a, 0.0))


def _leg(rig, pose, out, name, d_par, p):
    side = name[-1]
    target, foot_rot = pose.feet.get(side, (rig.ankle(side), np.eye(3)))
    if name.startswith('thigh'):
        k = knee(p, target, rig.len[name], rig.len['shin_' + side], np.array([0.0, 0.0, -1.0]))
        out['_knee_' + side] = k
        return rot_between(d_par @ rig.dir[name], k - p) @ d_par
    if name.startswith('shin'):
        return rot_between(d_par @ rig.dir[name], target - p) @ d_par
    return foot_rot


def fk(rig, pose):
    """คืน {กระดูก: (D, p)}"""
    out = {}
    for name in rig.order:
        par = rig.parent[name]
        if par is None:
            out[name] = (pose.local.get(name, np.eye(3)), rig.head[name] + pose.off)
            continue
        d_par, p_par = out[par]
        p = p_par + d_par @ (rig.head[name] - rig.head[par])
        if name in pose.absolute:
            d = pose.absolute[name]
        elif name.split('_')[0] in ('thigh', 'shin', 'foot') and name[-2:] in ('_L', '_R'):
            d = _leg(rig, pose, out, name, d_par, p)
        else:
            d = d_par @ pose.local.get(name, np.eye(3))
        out[name] = (d, p)
    return {k: v for k, v in out.items() if not k.startswith('_')}


def apply_point(rig, posed, bone, x):
    d, p = posed[bone]
    return d @ (np.asarray(x, dtype=float) - rig.head[bone]) + p


def transform4(rig, posed, bone):
    """เมทริกซ์ 4x4 ของการแปลงท่าของกระดูก (กรอบนก)"""
    d, p = posed[bone]
    m = np.eye(4)
    m[:3, :3] = d
    m[:3, 3] = p - d @ rig.head[bone]
    return m


TO_BLENDER = np.array([[1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=float)


def basis_matrices(rig, posed, rest_bl):
    """matrix_basis ของทุกกระดูกในกรอบ Blender : basis = rest⁻¹ · T_แม่⁻¹ · T · rest"""
    t_bl = {n: TO_BLENDER @ transform4(rig, posed, n) @ TO_BLENDER.T for n in rig.order}
    out = {}
    for n in rig.order:
        par = rig.parent[n]
        rel = t_bl[n] if par is None else np.linalg.inv(t_bl[par]) @ t_bl[n]
        out[n] = np.linalg.inv(rest_bl[n]) @ rel @ rest_bl[n]
    return out

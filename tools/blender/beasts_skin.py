"""ผิวเมชตามท่าแบบ numpy (linear blend skinning เหมือน Armature ของ Blender) : ใช้แก้ท่า (ตัวแนบพื้น) และวัดผลโดยไม่ต้องเข้า Blender"""
import numpy as np

from birds_pose import transform4


class Skin:
    """verts (n×3 กรอบสัตว์) · weights = [{กระดูก: น้ำหนัก}] ขนานกับ verts"""

    def __init__(self, rig, verts, weights):
        self.rig = rig
        self.bones = list(rig.order)
        col = {b: i for i, b in enumerate(self.bones)}
        self.w = np.zeros((len(verts), len(self.bones)))
        for vi, wd in enumerate(weights):
            for b, v in wd.items():
                self.w[vi, col[b]] += v
        total = self.w.sum(axis=1, keepdims=True)
        self.w = self.w / np.where(total > 0, total, 1.0)
        self.v4 = np.concatenate([np.asarray(verts, dtype=float), np.ones((len(verts), 1))], axis=1)

    def posed(self, posed):
        """ตำแหน่งจุดยอดทั้งหมดตามท่า (n×3)"""
        out = np.zeros((len(self.v4), 3))
        for i, b in enumerate(self.bones):
            wi = self.w[:, i]
            if not wi.any():
                continue
            m = transform4(self.rig, posed, b)
            out += wi[:, None] * (self.v4 @ m.T)[:, :3]
        return out

    def members(self, group, min_w):
        idx = [self.bones.index(b) for b in group if b in self.bones]
        return np.where(self.w[:, idx].sum(axis=1) >= min_w)[0]

    def min_y(self, posed, group, min_w=0.5):
        co = self.posed(posed)
        return float(co[self.members(group, min_w), 1].min())

"""น้ำหนักกระดูกของสัตว์สี่ขา Meshy (numpy ไม่รู้จัก Blender) · แนวเดียวกับ gardener_meshy_weights (automatic weights ใช้ไม่ได้กับเมช Meshy)
1) ติดป้ายกระดูกต่อจุดยอดตามเขต (ค่าใน quad_meshy_<ตัว>.json หัวข้อ weights · พิกัด glTF เมตร) :
   ขา = ต่ำกว่า legs.<F|H>.topY ในช่วง z ของคู่ขา ฝั่งเดียวกัน และใกล้แกนขาไม่เกิน radiusM → ท่อนขาที่ใกล้สุด
   ลำตัว/คอ/หัว = ท่อนที่ใกล้สุด (ต้นแขน/ต้นขาบวกระยะ upperLegBiasM ให้กินสีข้างน้อยลง)
   หาง = หลัง tail.fromZ และใกล้แกนหาง · หู = ใกล้แกนหู · ขากรรไกร = ใต้เส้นปาก (lip) ช่วงหน้า · เขี้ยว (rigidBoxes) = หัวล้วน ล็อก
   ขนแผงหลัง = สูงเหนือผิวหลัง (mane.surface) : ส่วนที่ชี้ขึ้นได้ hackles ตามความสูง (ส่วนหน้า mane.toZ ใช้ท่อนที่ใกล้สุด)
2) เกลี่ยรอบข้อต่อ (blendPairs : ลูก → [แม่, รัศมี ม.] ตามระยะบนแกนกระดูกลูก) แล้วเกลี่ยบนกราฟของเมช smoothIters รอบ
3) ตัดขาข้ามฝั่ง/ขาขึ้นสูงเกิน legMaxY · normalize"""
import numpy as np

SIDES = ('L', 'R')


def tail_bones(rig):
    """กระดูกหางทั้งสาย tail1, tail2, ... (โครงเดิม = tail1-3 · cat2 มีมากกว่า)"""
    return [n for n in rig.order if n.startswith('tail') and n[4:].isdigit()]


def _with_side(names, rig, side):
    return [n + '_' + side if n + '_' + side in rig.head else n for n in names]


def seg_dist(p, a, b):
    ab = b - a
    t = np.clip((p - a) @ ab / max(ab @ ab, 1e-12), 0.0, 1.0)
    return np.linalg.norm(p - (a + t[:, None] * ab), axis=1)


def _nearest(p, rig, names, bias=None):
    bias = bias or {}
    d = np.column_stack([seg_dist(p, rig.head[n], rig.tail[n]) + bias.get(n, 0.0) for n in names])
    return np.array(names, dtype=object)[d.argmin(1)], d.min(1)


def _side_mask(pos, side, tol=0.0):
    return pos[:, 0] * (1.0 if side == 'L' else -1.0) >= -tol


def _interp(pts, z):
    pts = np.asarray(pts, dtype=float)
    return np.interp(z, pts[:, 0], pts[:, 1])


def _legs(pos, rig, c, lab, todo):
    for pair, chain in (('F', ('upperarm', 'forearm', 'frontfoot', 'fronttoe')), ('H', ('thigh', 'shin', 'hindfoot', 'hindtoe'))):
        lc = c['legs'][pair]
        for side in SIDES:
            m = todo & _side_mask(pos, side) & (pos[:, 1] < lc['topY'])
            m &= (pos[:, 2] > lc['zMin']) & (pos[:, 2] < lc['zMax'])
            names = [b + '_' + side for b in chain]
            near, d = _nearest(pos[m], rig, names)
            ok = d < lc['radiusM']
            idx = np.nonzero(m)[0][ok]
            lab[idx] = near[ok]
            todo[idx] = False


def _torso(pos, rig, c, lab, todo):
    core = ['pelvis', 'spine', 'chest', 'neck1', 'neck2', 'head'] + c.get('coreExtra', [])  # bb : coreExtra = ข้อหลังที่เพิ่ม (cat2)
    # bb (แมว) : จุดสูงเกิน upperarmMaxY หรือหน้ากว่า upperarmMaxZ (แก้ม/ขนคอ) ห้ามเป็นต้นแขน/ต้นขา
    # ไม่งั้น clamp ตัดน้ำหนักขาทิ้งแล้วเติมกลับเป็นป้ายเดิม 100% → แก้มขยับตามขา (ไม่มีค่า = แบบ pp3 เดิม)
    no_leg = np.zeros(len(pos), dtype=bool)
    if 'upperarmMaxZ' in c:
        no_leg = ((pos[:, 1] > c['upperarmMaxY']) & (pos[:, 2] > 0)) | (pos[:, 2] > c['upperarmMaxZ'])
    for side in SIDES:
        for core_only in (False, True):
            m = todo & _side_mask(pos, side) & (no_leg == core_only)
            names = core if core_only else core + ['upperarm_' + side, 'thigh_' + side]
            bias = {'upperarm_' + side: c['upperLegBiasM'], 'thigh_' + side: c['upperLegBiasM']}
            lab[m] = _nearest(pos[m], rig, names, bias)[0]
            todo[m] = False


def _tail(pos, rig, c, lab):
    tc = c['tail']
    behind = pos[:, 2] < tc['fromZ']
    # bb (แมว) : หางพุ่มม้วนมาเหนือหลังถึงกลางตัว → สูงเกิน aboveY ในช่วงหลัง aboveMaxZ ก็เป็นหาง (ไม่มีค่า = แบบ pp3 เดิม)
    # aboveY เป็นตัวเลข = ระดับเดียว · เป็นรายการ [[z, y]] = ระดับไล่ตาม z (กันขนหลังช่วงกลางตัวที่สูงกว่าโคนหางถูกนับเป็นหาง)
    if 'aboveY' in tc:
        above = tc['aboveY'] if np.isscalar(tc['aboveY']) else _interp(tc['aboveY'], pos[:, 2])
        behind |= (pos[:, 1] > above) & (pos[:, 2] < tc['aboveMaxZ'])
    m = behind & (np.abs(pos[:, 0]) < tc['halfWidthM'])
    near, d = _nearest(pos[m], rig, tail_bones(rig))
    ok = d < tc['radiusM']
    lab[np.nonzero(m)[0][ok]] = near[ok]


def _ear_mask(pos, rig, ec, lab, side):
    """จุดของใบหู : ใกล้กระดูกหู + ไม่ชิดกลางหัว
    bb (แมว) : ใบหูอยู่หลังเส้นแบ่งหัว/คอ → ป้ายเดิมเป็น neck2 · fromBones = ป้ายที่ยอมให้หูแย่งได้ (ไม่มี = head อย่างเดียวแบบ pp3)
    maxDzM / minY = ใบหูบางและตั้งขึ้น : ตัดขนหน้าผากด้านหน้าและหัวใต้โคนหูออก (ไม่มี = ไม่ตัด)"""
    head, tip = rig.head['ear_' + side], rig.tail['ear_' + side]
    ok = np.isin(lab, ec.get('fromBones', ['head'])) & _side_mask(pos, side)
    ok &= (seg_dist(pos, head, tip) < ec['radiusM']) & (np.abs(pos[:, 0]) > ec['minAbsX'])
    if 'maxDzM' in ec:
        ok &= np.abs(pos[:, 2] - (head[2] + tip[2]) / 2) < ec['maxDzM']
    if 'minY' in ec:
        ok &= pos[:, 1] > ec['minY']
    return ok


def _scapula(pos, rig, c, lab):
    """bb (cat2) : จุดใกล้แกนสะบัก (weights.scapula) ที่ป้ายเดิมอยู่ใน fromBones (ชื่อไม่มีข้าง = ใช้ข้างนั้น) → scapula_<ข้าง>"""
    sc = c.get('scapula')
    if not sc:
        return
    for side in SIDES:
        bone = 'scapula_' + side
        ok = np.isin(lab, _with_side(sc['fromBones'], rig, side)) & _side_mask(pos, side)
        ok &= (seg_dist(pos, rig.head[bone], rig.tail[bone]) < sc['radiusM']) & (np.abs(pos[:, 0]) > sc['minAbsX'])
        lab[ok] = bone


def _ear_tip(pos, rig, lab):
    """bb (cat2) : จุดของใบหูที่เลยหัวกระดูก eartip ไปทางปลาย → eartip_<ข้าง> (ไม่มีกระดูก = ไม่ทำ)"""
    for side in SIDES:
        tip = 'eartip_' + side
        if tip not in rig.head:
            continue
        idx = np.nonzero(lab == 'ear_' + side)[0]
        t = (pos[idx] - rig.head[tip]) @ rig.dir[tip]
        lab[idx[t > 0]] = tip


def _head_parts(pos, rig, c, lab, rigid):
    for side in SIDES:
        lab[_ear_mask(pos, rig, c['ear'], lab, side)] = 'ear_' + side
    _ear_tip(pos, rig, lab)
    jc = c['jaw']
    jaw = (lab == 'head') & (pos[:, 2] > jc['fromZ']) & (pos[:, 1] < _interp(jc['lip'], pos[:, 2]))
    jaw &= np.abs(pos[:, 0]) < jc['halfWidthM']
    lab[jaw] = 'jaw'
    for box in c['rigidBoxes']:
        p = pos.copy()
        if box.get('mirrorX'):
            p[:, 0] = np.abs(p[:, 0])
        inside = np.all((p >= np.asarray(box['min'])) & (p <= np.asarray(box['max'])), axis=1)
        lab[inside] = box['bone']
        rigid |= inside


def label(pos, rig, c):
    """(ป้ายชื่อกระดูกต่อจุด, มาสก์เขตแข็งที่ล็อกตอนเกลี่ย)"""
    lab = np.empty(len(pos), dtype=object)
    todo = np.ones(len(pos), dtype=bool)
    rigid = np.zeros(len(pos), dtype=bool)
    _legs(pos, rig, c, lab, todo)
    _torso(pos, rig, c, lab, todo)
    _scapula(pos, rig, c, lab)
    _tail(pos, rig, c, lab)
    _head_parts(pos, rig, c, lab, rigid)
    return lab, rigid


def _smooth(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def _pairs(rig, c):
    """blendPairs ที่ขยายชื่อ _L/_R แล้ว → [(ลูก, แม่, รัศมี)]"""
    out = []
    for child, (parent, radius) in c['blendPairs'].items():
        if child in rig.head:
            out.append((child, parent, radius))
            continue
        for s in SIDES:
            par = parent + '_' + s if parent + '_' + s in rig.head else parent
            out.append((child + '_' + s, par, radius))
    return out


def blend(pos, lab, rigid, rig, c):
    col = {n: k for k, n in enumerate(rig.order)}
    w = np.zeros((len(pos), len(rig.order)))
    w[np.arange(len(pos)), [col[x] for x in lab]] = 1.0
    for child, parent, radius in _pairs(rig, c):
        t = (pos - rig.head[child]) @ rig.dir[child]
        zone = ((lab == child) | (lab == parent)) & (np.abs(t) < radius) & ~rigid
        k = _smooth((t[zone] + radius) / (2 * radius))
        w[zone] = 0.0
        w[zone, col[child]], w[zone, col[parent]] = k, 1.0 - k
    return w


def mane(w, pos, lab, rig, c):
    """ขนแผงหลังที่สูงเหนือผิว : ย้ายน้ำหนักไป hackles ตามความสูง (แก้ในที่) · คืนจำนวนจุด"""
    mc = c['mane']
    above = pos[:, 1] - _interp(mc['surface'], pos[:, 2])
    sel = (above > 0) & (pos[:, 2] < mc['toZ']) & (pos[:, 2] > mc['fromZ']) & np.isin(lab, mc['fromBones'])
    k = _smooth(above[sel] / mc['spanM'])[:, None]
    hk = rig.order.index('hackles')
    w[sel] *= 1.0 - k
    w[sel, hk] += k[:, 0]
    return int(sel.sum())


def diffuse(w, edges, iters, lock):
    """เกลี่ยกับเพื่อนบ้านบนกราฟ (ครึ่งต่อครึ่ง) · จุดใน lock คงค่าเดิม"""
    n = len(w)
    deg = np.bincount(edges.ravel(), minlength=n).astype(float)
    v, base = w.copy(), w.copy()
    for _ in range(iters):
        acc = np.zeros_like(v)
        np.add.at(acc, edges[:, 0], v[edges[:, 1]])
        np.add.at(acc, edges[:, 1], v[edges[:, 0]])
        v = 0.5 * v + 0.5 * acc / np.maximum(deg, 1)[:, None]
        v[lock] = base[lock]
    return v


def clamp(w, pos, lab, rig, c):
    """ขาไม่ข้ามฝั่ง (เกิน legCrossM) · ขาไม่สูงเกิน legMaxY · จุดที่ว่าง = ป้ายเดิม · normalize"""
    for side in SIDES:
        cols = [rig.order.index(n) for n in rig.order if n.endswith('_' + side) and not n.startswith('ear')]
        w[np.ix_(~_side_mask(pos, side, c['legCrossM']), cols)] = 0.0
    legs = [rig.order.index(n) for n in rig.leg_of]
    w[np.ix_(pos[:, 1] > c['legMaxY'], legs)] = 0.0
    w[w < c['minWeight']] = 0.0
    empty = w.sum(1) <= 1e-9
    w[empty, [rig.order.index(x) for x in lab[empty]]] = 1.0
    return w / w.sum(1, keepdims=True)


def limit(w, count):
    """เก็บ count ตัวที่มากสุดต่อจุด (glTF 4 ตัว) แล้ว normalize"""
    idx = np.argsort(-w, axis=1)[:, count:]
    np.put_along_axis(w, idx, 0.0, axis=1)
    return w / w.sum(1, keepdims=True)


def _piece_labels(pos, rig, lab, piece, core_extra):
    """bb : ชิ้นหางแยก (quad_meshy_tailsplit) → ป้ายกระดูกหางที่ใกล้สุด · ตัวที่ติดป้ายหาง → ท่อนแกนกลางที่ใกล้สุด"""
    tail = tail_bones(rig)
    lab[piece] = _nearest(pos[piece], rig, tail)[0]
    stray = ~piece & np.isin(lab, tail)
    lab[stray] = _nearest(pos[stray], rig, ['pelvis', 'spine', 'chest'] + core_extra)[0]


def _piece_split(w, rig, lab, piece):
    """bb : ชิ้นหาง = กระดูกหางล้วน · ตัว = ห้ามกระดูกหาง (หางหมุนแล้วผิวตัวไม่ยืดตาม) · ว่าง = ป้ายเดิม"""
    cols = [rig.order.index(n) for n in tail_bones(rig)]
    keep = np.zeros(w.shape[1], dtype=bool)
    keep[cols] = True
    w[np.ix_(piece, ~keep)] = 0.0
    w[np.ix_(~piece, keep)] = 0.0
    empty = w.sum(1) <= 1e-9
    w[empty, [rig.order.index(x) for x in lab[empty]]] = 1.0
    return w / w.sum(1, keepdims=True)


def compute(pos, edges, rig, c, piece=None):
    """น้ำหนักแบบแน่น (N, กระดูก ตามลำดับ rig.order) + รายงาน · piece = จุดของชิ้นหางแยก (None = ไม่มี)"""
    lab, rigid = label(pos, rig, c)
    if piece is not None:
        _piece_labels(pos, rig, lab, piece, c.get('coreExtra', []))
    w = blend(pos, lab, rigid, rig, c)
    n_mane = mane(w, pos, lab, rig, c)
    w = diffuse(w, edges, c['smoothIters'], rigid)
    w = clamp(w, pos, lab, rig, c)
    if piece is not None:
        w = _piece_split(w, rig, lab, piece)
    w = limit(w, c['maxInfluences'])
    names, counts = np.unique(lab.astype(str), return_counts=True)
    rep = {'rigidVerts': int(rigid.sum()), 'maneVerts': n_mane, 'labels': dict(zip(names.tolist(), counts.tolist()))}
    return w, rep


def as_dicts(w, names):
    """[{กระดูก: น้ำหนัก}] ต่อจุด (สำหรับ beasts_skin.Skin / vertex group)"""
    out = []
    for row in w:
        nz = np.nonzero(row)[0]
        out.append({names[k]: float(row[k]) for k in nz})
    return out

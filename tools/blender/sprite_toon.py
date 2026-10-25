"""ลุคภาพวาดของภาพ 2.5D (sprite_render.py) : ลงสีการ์ตูนเป็นขั้น + เส้นขอบ
สี : แสงที่ตกบนผิว (Diffuse → Shader to RGB) ตัดเป็นขั้นด้วย ColorRamp แบบคงที่ คูณสีผิวเดิม → Emission (สีไม่ขึ้นกับแสงอีกชั้น)
เส้นขอบ : เปลือกกลับด้าน (Solidify ตัวเลขหนาติดลบ + flip normal + ซ่อนหน้าหลัง) ต่อท้าย modifier กระดูก → ขยับตามท่า"""
import bpy

OUTLINE = 'sprite_outline'


def _base_tex(mat):
    for n in mat.node_tree.nodes:
        if n.type == 'BSDF_PRINCIPLED' and n.inputs['Base Color'].links:
            return n.inputs['Base Color'].links[0].from_socket
    return None


def _ramp(nt, steps):
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.interpolation = 'CONSTANT'
    els = ramp.color_ramp.elements
    while len(els) > 1:
        els.remove(els[-1])
    for k, (pos, value) in enumerate(steps):
        el = els[0] if k == 0 else els.new(pos)
        el.position = pos
        el.color = (value, value, value, 1.0)
    return ramp


def toon_material(mat, tc):
    """แทนผิวเดิมด้วยสีขั้น (ไม่มีภาพผิว = ไม่แก้)"""
    nt = mat.node_tree
    tex = _base_tex(mat)
    if tex is None:
        return False
    diff = nt.nodes.new('ShaderNodeBsdfDiffuse')
    to_rgb = nt.nodes.new('ShaderNodeShaderToRGB')
    ramp = _ramp(nt, tc['steps'])
    mul = nt.nodes.new('ShaderNodeMix')
    mul.data_type = 'RGBA'
    mul.blend_type = 'MULTIPLY'
    mul.inputs['Factor'].default_value = 1.0
    emit = nt.nodes.new('ShaderNodeEmission')
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(diff.outputs['BSDF'], to_rgb.inputs['Shader'])
    nt.links.new(to_rgb.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(tex, mul.inputs['A'])
    nt.links.new(ramp.outputs['Color'], mul.inputs['B'])
    nt.links.new(mul.outputs['Result'], emit.inputs['Color'])
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    return True


def outline_material(tc):
    mat = bpy.data.materials.new(OUTLINE)
    mat.use_nodes = True
    nt = mat.node_tree
    emit = nt.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value = list(tc['outlineColor']) + [1.0]
    out = next(n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL')
    nt.links.new(emit.outputs['Emission'], out.inputs['Surface'])
    mat.use_backface_culling = True
    return mat


def add_outline(obj, tc):
    """เปลือกเส้นขอบเป็นวัสดุช่องใหม่ของเมชเดิม (material_offset) · หนา outlineM เมตร"""
    obj.data.materials.append(outline_material(tc))
    mod = obj.modifiers.new('outline', 'SOLIDIFY')
    mod.thickness = -tc['outlineM']
    mod.offset = 1.0
    mod.use_flip_normals = True
    mod.use_rim = False
    mod.material_offset = len(obj.data.materials) - 1


def apply(tc):
    """ทุกเมชในฉาก · คืนจำนวนวัสดุที่แปลง"""
    n = 0
    for obj in [o for o in bpy.data.objects if o.type == 'MESH']:
        for mat in list(obj.data.materials):
            if mat and mat.use_nodes and toon_material(mat, tc):
                mat.use_backface_culling = True
                n += 1
        add_outline(obj, tc)
    return n

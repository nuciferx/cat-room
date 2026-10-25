"""วัสดุสัตว์สี่ขา Meshy (Blender) : ภาพ basecolor + normal ที่อบใหม่ (quad_meshy_bake) · ไม่ใช้ภาพ metallicRoughness ของต้นทาง
(ต้นทาง metallicFactor 1 ทำให้มันวาว) → metallic 0 · roughness ค่าเดียวสูง · specular ต่ำ (ขนด้าน) · doubleSided ตามค่า"""
import bpy


def make(images, mc, name):
    """images = {'base': ภาพ, 'normal': ภาพ} → (วัสดุ, รายงาน)"""
    mat = bpy.data.materials.new(name + '_hair')
    mat.use_nodes = True
    mat.use_backface_culling = not mc['doubleSided']
    nt = mat.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = images['base']
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    ntex = nt.nodes.new('ShaderNodeTexImage')
    ntex.image = images['normal']
    nmap = nt.nodes.new('ShaderNodeNormalMap')
    nmap.inputs['Strength'].default_value = mc['normalStrength']
    nt.links.new(ntex.outputs['Color'], nmap.inputs['Color'])
    nt.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = mc['roughness']
    bsdf.inputs['Specular IOR Level'].default_value = mc['specular']
    return mat, {'roughness': mc['roughness'], 'metallic': 0.0, 'specular': mc['specular'], 'doubleSided': mc['doubleSided']}

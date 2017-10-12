import pymel.core as pc
import re
import glob
import os.path
import yaml
import random


fe_noise_expr = ('\n$fe = %d + int(abs(noise(frame * %s + %d)) * '
                 '((%d - %d) + 0.999));')

fe_expr = '\n$fe = %d + ((int)(frame * %s + %d) %% (%d + 1 - %d));'
fe_assign_expr = '\n%s.frameExtension = $fe;'
param_expr = '\nif ( $fe == %d ) { %s = %f; }'
param_assign_expr = '\n%s = %s;'


def loadAssetList(list_file):
    lines = []
    with open(list_file) as _file:
        for line in _file.readlines():
            if not line.startswith('--'):
                line = line.replace('\t', ' '*4)
                line = re.sub(r'\{\s*(\d+)\s*,\s*(\d+)\s*\}', r'[ \1, \2]',
                              line)
                lines.append(line.replace('=', ':'))
    data = yaml.load('\n'.join(lines))
    return data['assetlist']


def make2dTextureSequence(seq, nums, assetlist=None, resolution=None):
    dirname, basename, ext = seq
    file_name = os.path.join(dirname, '.'.join([basename, nums[0], ext]))
    file_node = pc.mel.createRenderNodeCB("-as2DTexture", "", "file", "")
    file_node = pc.PyNode(file_node)
    file_node.defaultColor.set((0, 0, 0))
    file_node.ftn.set(file_name)
    file_node.useFrameExtension.set(True)

    if assetlist is None:
        assetlist = loadAssetList(os.path.join(dirname, 'list.txt'))
    if resolution is None:
        resolution = (2632, 1510)
    resU, resV = resolution

    place_node = file_node.coverage.inputs()[0]
    place_node.wrapU.set(False)

    pc.addAttr(place_node, ln='frequency', at='double', dv=0.5)

    pc.delete(file_node.fe.inputs())
    nums_ = [int(num) for num in nums]
    _min, _max = min(nums_), max(nums_)
    expr = fe_expr % (_min, place_node.frequency.name(),
                      random.randint(0, 100), _max, _min)

    for i, num in enumerate(nums):
        data = assetlist['.'.join([basename, num])]
        sizeU, sizeV = data['size']
        posU, posV = data['pos']

        if i == 0:
            expr += param_assign_expr % ('$coverageU', float(sizeU)/resU)
            expr += param_assign_expr % ('$coverageV', float(sizeV)/resV)
            expr += param_assign_expr % ('$translateFrameV', float(posV)/resV)
            expr += param_assign_expr % ('$translateFrameU',
                                         1-float(sizeU+posU)/resU)

        expr += param_expr % (int(num), '$coverageU',
                              float(sizeU)/resU)
        expr += param_expr % (int(num), '$coverageV',
                              float(sizeV)/resV)
        expr += param_expr % (int(num), '$translateFrameU',
                              float(posU)/resU)
        expr += param_expr % (int(num), '$translateFrameV',
                              1-float(posV+sizeV)/resV)

    expr += param_assign_expr % (place_node.coverageU,
                                 '$coverageU')
    expr += param_assign_expr % (place_node.coverageV,
                                 '$coverageV')
    expr += param_assign_expr % (place_node.translateFrameU,
                                 '$translateFrameU')
    expr += param_assign_expr % (place_node.translateFrameV,
                                 '$translateFrameV')
    expr += fe_assign_expr % file_node
    pc.expression(s=expr)

    multiply_node = pc.shadingNode('multiplyDivide', asUtility=True)
    file_node.outColor.connect(multiply_node.input1)
    reverse_node = pc.shadingNode('reverse', asUtility=True)
    file_node.outTransparency.connect(reverse_node.input)
    reverse_node.output.connect(multiply_node.input2)

    return file_node


def loadAnimatableTextureSequences(dirname, resolution=None):

    seqs = {}
    seqs_fc = {}
    parts_exp = {}

    for _file in glob.glob(os.path.join(dirname, '*.png')):
        _file = os.path.normpath(_file)
        match = re.match(
                '(.*)' + (os.sep if os.sep == '/' else os.sep * 2) +
                '(.*)\.(\d+)\.(.*)', _file)

        if match:
            dirname, basename, number, ext = match.groups()
            seq = (dirname, basename, ext)

            if seq not in seqs:
                seqs[seq] = [number]

                try:
                    part, exp = basename.split('-')
                    exps = parts_exp.get(part, [])
                    exps.append(seq)
                    parts_exp[part] = exps
                except ValueError:
                    parts_exp[basename] = [seq]

            else:
                nums = seqs[seq]
                nums.append(number)

    for seq, nums in seqs.items():
        file_node = make2dTextureSequence(seq, nums)
        seqs_fc[seq] = (file_node, [int(num) for num in nums])

    return seqs_fc, parts_exp


def layer_textures(seqs_fc, parts_exp):
    main_texture = pc.shadingNode('layeredTexture', asTexture=True)
    main_texture.attr('inputs')[0].color.set(0, 0, 0)
    main_texture.attr('inputs')[0].isVisible.set(False)
    main_texture.attr('inputs')[0].blendMode.set(8)

    part_textures = {}

    for num, (part, exps) in enumerate(parts_exp.items()):
        layered_texture = pc.shadingNode('layeredTexture', asTexture=True)

        for num_exp, exp in enumerate(exps):
            file_node, _ = seqs_fc[exp]

            multiply_node = file_node.outColor.outputs()[0]
            multiply_node.output.connect(
                    layered_texture.attr('inputs')[num_exp].color)

        layered_texture.outColor.connect(
                main_texture.attr('inputs')[num+1].color)
        part_textures[part] = layered_texture
        main_texture.attr('inputs')[num+1].blendMode.set(8)

    return main_texture, part_textures


def connect_screen_texture_control(tex_dir, screen_n_ctrl=None):
    if screen_n_ctrl is None:
        screen_n_ctrl = pc.ls(sl=True, o=True)[:2]
    try:
        screen, control = screen_n_ctrl
    except ValueError:
        pc.error('Please select screen and control')

    seqs, parts = loadAnimatableTextureSequences(tex_dir)
    main_texture, part_textures = layer_textures(seqs, parts)
    pc.select(screen)
    pc.mel.createAndAssignShader("surfaceShader", "")
    engine = screen.getShape(type='mesh').outputs(type="shadingEngine")[0]
    shader = engine.surfaceShader.inputs()[0]
    main_texture.outColor.connect(shader.outColor)

    pc.addAttr(control, ln='switch', at='bool', dv=True, keyable=True)
    control.switch.connect(main_texture.attr('inputs')[0].isVisible)

    pc.addAttr(control, ln='frequency', at='double', dv=0.5, keyable=True)
    for part, exps in parts.items():
        part_texture = part_textures[part]
        pc.select(control)
        pc.addAttr(ln=part, at="long", min=0, max=len(exps)-1, dv=0,
                   hasMaxValue=True, hasMinValue=True, keyable=True)
        for num, exp in enumerate(exps):
            file_node = seqs[exp][0]
            place_node = file_node.coverage.inputs()[0]
            control.frequency.connect(place_node.frequency)
            switch_expr = ("%s.inputs[%d].isVisible = (%s==%d) ? 1: 0;")
            switch_expr = switch_expr % (
                    part_texture.name(), num, control.name() + '.' + part, num)
            pc.expression(s=switch_expr)


if __name__ == "__main__":
    pc.openFile('D:/temp/elephant/scenes/smart_car_aaber_rig.ma', f=True)
    pc.select(['screen_geo', 'screen_ctrl'])
    screen, control = pc.ls(sl=True, o=True)
    tex_dir = r'd:/temp/pics/'
    connect_screen_texture_control(tex_dir, (screen, control))
    pc.select(control)

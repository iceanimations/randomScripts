import pymel.core as pc
import re
import glob
import os.path
import yaml
import random


noise_expr = ("%s.frameExtension = %d + int(abs(noise(frame + %d)) *"
              " ((%d - %d) + 0.999));")


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


def make2dTextureSequence(file_name, data, resolution=None):
    file_node = pc.mel.createRenderNodeCB("-as2DTexture", "", "file", "")
    file_node = pc.PyNode(file_node)
    file_node.defaultColor.set((0, 0, 0))
    file_node.ftn.set(file_name)
    file_node.useFrameExtension.set(True)

    if resolution is None:
        resolution = (2632, 1510)
    sizeU, sizeV = data['size']
    posU, posV = data['pos']
    resU, resV = resolution

    place_node = file_node.coverage.inputs()[0]
    place_node.coverageU.set(float(sizeU)/resU)
    place_node.coverageV.set(float(sizeV)/resV)
    place_node.translateFrameU.set(float(posU)/resU)
    place_node.translateFrameV.set(1-(float(sizeV+posV)/resV))
    place_node.wrapU.set(False)

    multiply_node = pc.shadingNode('multiplyDivide', asUtility=True)
    file_node.outColor.connect(multiply_node.input1)
    reverse_node = pc.shadingNode('reverse', asUtility=True)
    file_node.outTransparency.connect(reverse_node.input)
    reverse_node.output.connect(multiply_node.input2)

    return file_node


def loadAnimatableTextureSequences(dirname, resolution=None):
    assetlist = loadAssetList(os.path.join(dirname, 'list.txt'))

    seqs_fc = {}
    parts_exp = {}

    for _file in glob.glob(os.path.join(dirname, '*.png')):
        _file = os.path.normpath(_file)
        match = re.match('(.*)' + os.sep * 2 + '(.*)\.(\d+)\.(.*)', _file)

        if match:
            dirname, basename, number, ext = match.groups()
            seq = (dirname, basename, ext)

            if seq not in seqs_fc:
                file_node = make2dTextureSequence(
                        _file, assetlist['.'.join([basename, number])])
                seqs_fc[seq] = (file_node, [int(number)])

                try:
                    part, exp = basename.split('-')
                    exps = parts_exp.get(part, [])
                    exps.append(seq)
                    parts_exp[part] = exps
                except ValueError:
                    parts_exp[basename] = [seq]

            else:
                file_node, nums = seqs_fc[seq]
                nums.append(int(number))

    return seqs_fc, parts_exp


def layer_textures(seqs_fc, parts_exp):
    main_texture = pc.shadingNode('layeredTexture', asTexture=True)
    part_textures = {}

    for num, (part, exps) in enumerate(parts_exp.items()):
        layered_texture = pc.shadingNode('layeredTexture', asTexture=True)

        for num_exp, exp in enumerate(exps):
            file_node, frames = seqs_fc[exp]
            _min, _max = min(frames), max(frames)

            pc.delete(file_node.frameExtension.inputs())
            exp_str = noise_expr % (
                file_node.name(), _min, random.randint(0, 1000), _max, _min)
            pc.expression(s=exp_str)

            multiply_node = file_node.outColor.outputs()[0]
            multiply_node.output.connect(
                    layered_texture.attr('inputs')[num_exp].color)

        layered_texture.outColor.connect(
                main_texture.attr('inputs')[num].color)
        part_textures[part] = layered_texture
        main_texture.attr('inputs')[num].blendMode.set(8)

    return main_texture, part_textures


def connect_screen_texture_control(tex_dir, screen_n_ctrl):
    try:
        screen, control = pc.ls(sl=True, o=True)[:2]
    except ValueError:
        pc.error('Please select screen and control')
    seqs, parts = loadAnimatableTextureSequences(tex_dir)
    main_texture, part_textures = layer_textures(seqs, parts)
    print main_texture, type(main_texture)
    pc.select(screen)
    pc.mel.createAndAssignShader("surfaceShader", "")
    engine = screen.getShape(type='mesh').outputs(type="shadingEngine")[0]
    shader = engine.surfaceShader.inputs()[0]
    main_texture.outColor.connect(shader.outColor)

    for part, exps in parts.items():
        part_texture = part_textures[part]
        pc.select(control)
        pc.addAttr(ln=part, at="long", min=0, max=len(exps)-1, dv=0,
                   hasMaxValue=True, hasMinValue=True, keyable=True)
        for num, exp in enumerate(exps):
            switch_expr = ("%s.inputs[%d].isVisible = (%s==%d) ? 1: 0;")
            switch_expr = switch_expr % (
                    part_texture.name(), num, control.name() + '.' + part, num)
            pc.expression(s=switch_expr)


if __name__ == "__main__":
    pc.openFile('D:/temp/elephant/scenes/smart_car_02.ma', f=True)
    pc.select(['screen_geo', 'screen_ctrl'])
    screen, control = pc.ls(sl=True, o=True)
    tex_dir = r'd:/temp/pics/'
    connect_screen_texture_control(tex_dir, (screen, control))

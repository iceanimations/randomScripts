import pymel.core as pc
import re

def get_controls(sl=False):
    return [node.firstParent() for node in pc.ls(type='nurbsCurve', sl=sl)]

def rename_controls(removeCharPrefix=None, add_underscore_to_lr=True, controls=None):

    if controls is None:
        controls = get_controls()

    if removeCharPrefix:
        cp = re.compile(removeCharPrefix+ '_' )

    if add_underscore_to_lr:
        lr = re.compile('(_?r|l)([A-Z]{1})')

    for node in controls:

        locked = pc.lockNode(node, q=1)
        if locked:
            pc.lockNode(node, l=False)

        newname = unicode( node )
        sub = 0

        if removeCharPrefix:
            _newname, _sub = cp.subn('', newname )
            if _sub:
                newname = _newname
                sub += _sub

        if add_underscore_to_lr:
            _newname, _sub = lr.subn(r'\1_\2', newname)
            if _sub:
                newname = _newname
            sub += _sub

        if sub:
            print 'renaming', node, 'to', newname
            node.rename(newname)

        if locked:
            pc.lockNode(node, l=True)

class RigRenameGUI(object):
    name = 'RigRenameGUI'

    def __init__(self):
        if pc.window(self.name, exists=True):
            pc.deleteUI(self.name)
        with pc.window(self.name, title='Rig Renamer'):
            with pc.columnLayout(adj=True):
                self.charPrefixField = pc.textFieldGrp(label='Char_PrefixName')
                self.doUnderscoreCheck = pc.checkBoxGrp(v1=True,
                        label='add underscore to lr    ')
                self.useSelectionCheck = pc.checkBoxGrp(v1=False,
                        label='rename selected controls only    ')
                self.doButton = pc.button('Go', c=self.do)

    def do(self, *args):
        pre = self.charPrefixField.getText()
        und = self.doUnderscoreCheck.getValue1()
        sel = self.useSelectionCheck.getValue1()
        con = get_controls(sl=sel)
        rename_controls(removeCharPrefix=pre, add_underscore_to_lr=und,
                controls=con)




if __name__ == "__main__":
    # rename_controls(removeCharPrefix='Ch')
    RigRenameGUI()


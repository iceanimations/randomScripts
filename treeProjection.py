import pymel.core as pc

def treeProjection(object):
    group = object.getParent()
    facesList = [item.faces for item in group.getChildren()]
    pc.polyProjection(*facesList,ch=1,type="Planar",ibd=1, md='x')

for sel in pc.ls(sl=1):
    treeProjection(sel)

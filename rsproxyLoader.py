import pymel.core as pc
from collections import namedtuple
import os
import re

crowdDirectory = r'P:\external\Al_Mansour_Season_02\Test\Raheel\CrowdAnimation\CrowdRSProxy'
CrowdCycle = namedtuple('crowdCycle', 'path startFrame endFrame')

rsfilePattern = re.compile(r'(.*?\.?)(\d+)(\.rs)')


def findCrowdCycles(crowdDirectory=crowdDirectory):
    pathToNumbers = dict()
    for path, dirnames, filenames in os.walk(crowdDirectory):

        for phile in filenames:
            match = rsfilePattern.match(phile)
            if match:
                name, number, ext = match.groups()
                generic = rsfilePattern.sub(r'\1'+'#'*len(number)+r'\3', phile)
                filepath = os.path.join(path, generic)
                if not pathToNumbers.has_key(filepath):
                    pathToNumbers[filepath] = []
                pathToNumbers[filepath].append(int(number))

    crowdCycles = []
    for path, numbers in pathToNumbers.items():
        startFrame = min(numbers)
        endFrame = max(numbers)
        for num in range(startFrame, endFrame+1):
            if num not in numbers:
                endFrame = num-1
        crowdCycles.append(CrowdCycle(path, startFrame, endFrame))

    return crowdCycles

def makeRsProxyFromCrowdCycle(crowdCycle):
    proxy, mesh, transform = (pc.PyNode(nodename) for nodename in pc.mel.redshiftCreateProxy())
    proxy.fileName.set(crowdCycle.path)
    proxy.useFrameExtension.set(True)
    proxy.displayMode.set(1)
    return proxy, mesh, transform


if __name__ == '__main__':
    for crowdCycle in  findCrowdCycles():
        print makeRsProxyFromCrowdCycle(crowdCycle)

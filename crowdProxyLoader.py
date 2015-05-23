import pymel.core as pc
from collections import namedtuple
import os
import re
from string import Template

CrowdCycle = namedtuple('crowdCycle', 'path startFrame endFrame')
rsfilePattern = re.compile(r'(.*?\.?)(\d+)(\.rs)')

defaultCrowdDirectory = r'P:\external\Al_Mansour_Season_02\Test\Raheel\CrowdAnimation\CrowdRSProxy'
def findCrowdCycles(crowdDirectory=defaultCrowdDirectory):
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

cycleExpression = '''
int $startFrame = $s_startFrame;
int $endFrame = $s_endFrame;
int $offset = $s_offset;
int $duration = $endFrame - $startFrame + 1;
int $curFrame = $startFrame + (int(frame)+$offset)%($duration);
$s_proxyFrameExtension = $curFrame;
'''
def makeRsProxyFromCrowdCycle(crowdCycle, offset=0):
    proxy, mesh, transform = (pc.PyNode(nodename) for nodename in pc.mel.redshiftCreateProxy())
    proxy.fileName.set(crowdCycle.path)
    proxy.useFrameExtension.set(True)
    proxy.displayMode.set(1)
    data = {}
    data['s_startFrame']=str(crowdCycle.startFrame)
    data['s_endFrame']=str(crowdCycle.endFrame)
    data['s_offset']=str(offset)
    data['s_proxyFrameExtension']=str(proxy.frameExtension)
    pc.expression(s=Template(cycleExpression).safe_substitute(data))
    proxy.frameOffset.setLocked(True)
    proxy.useFrameExtension.setLocked(True)
    proxy.frameExtension.setLocked(True)
    return proxy, mesh, transform


def createCrowdCycleProxies(numOffsetsPerCycle=3):
    directory = pc.fileDialog2(fm=2, cap='Location of crowdCycles',
            startingDirectory=defaultCrowdDirectory, okc='Select Directory')
    if directory:
        cycles = findCrowdCycles(directory[0])
        mainProgressBar = pc.uitypes.PyUI(pc.MelGlobals.get('gMainProgressBar'))
        mainProgressBar.setMaxValue(len(cycles)*numOffsetsPerCycle)
        mainProgressBar.setIsInterruptable(True)
        mainProgressBar.beginProgress()
        try:
            for crowdCycle in cycles:
                step = int (float(crowdCycle.endFrame - crowdCycle.startFrame)
                        / numOffsetsPerCycle)
                for stepNumber in range(numOffsetsPerCycle):
                    offset = crowdCycle.startFrame + stepNumber * step
                    makeRsProxyFromCrowdCycle(crowdCycle, offset)
                    mainProgressBar.step()
                    if mainProgressBar.getIsCancelled():
                        break
                if mainProgressBar.getIsCancelled():
                    break
        finally:
            mainProgressBar.endProgress()


if __name__ == '__main__':
    defaultCrowdDirectory = r'P:\external\Al_Mansour_Season_02\Test\Raheel\CrowdAnimation\CrowdRSProxy'
    createCrowdCycleProxies(numOffsetsPerCycle=3)

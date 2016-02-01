from venture.lite.builtin import builtInSPs
from venture.mite.sp import SimpleRandomSPWrapper, SimpleDeterministicSPWrapper
from venture.mite.csp import make_csp

liteBuiltInSPs = builtInSPs

wrappedRandomSPs = [
    'beta',
    'flip',
]

wrappedDeterministicSPs = [
    'add',
]

def builtInSPs():
    spsList = []

    for sp in wrappedRandomSPs:
        spsList.append((sp, SimpleRandomSPWrapper(
            liteBuiltInSPs()[sp].outputPSP)))

    for sp in wrappedDeterministicSPs:
        spsList.append((sp, SimpleDeterministicSPWrapper(
            liteBuiltInSPs()[sp].outputPSP)))

    spsList.append(('make_csp', SimpleDeterministicSPWrapper(make_csp)))

    return spsList

"""Compare normalized closed uncertainty intervals; no clock calibration."""


def relation(a, b):
    for lo, hi in (a, b):
        if type(lo) is not int or type(hi) is not int or lo > hi:
            raise ValueError('expected ordered integer tick interval')
    if a[1] < b[0]:
        return 'before'
    if b[1] < a[0]:
        return 'after'
    return 'indeterminate'

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Derived from nsVersionComparator.cpp in mozilla-central

from itertools import izip_longest
import re


__all__ = 'Version', 'VersionPart'


def strcmp(a, b):
    # Null string comes after any non-null string
    if not a:
        return 1 if b else 0
    elif not b:
        return -1

    return cmp(a, b)


class VersionPart(object):
    numA   = 0
    strB   = ''
    numC   = 0
    extraD = ''

    def __init__(self, part):
        self._part = part

        if part == '*':
            self.numA = float('inf')
        else:
            self.numA, self.strB = self._splitnum(part)

        if self.strB:
            if self.strB[0] == '+':
                self.numA += 1
                self.strB = 'pre'
            else:
                match = re.match(r'([^\d+-]*)(.*)', self.strB)

                self.strB = match.group(1)
                self.numC, self.extraD = self._splitnum(match.group(2))

    def __repr__(self):
        return 'VersionPart(%s)' % repr(self._part)

    def __str__(self):
        return self._part

    def __cmp__(self, other):
        if other is None:
            return 1

        return (cmp(self.numA, other.numA) or
                strcmp(self.strB, other.strB) or
                cmp(self.numC, other.numC) or
                strcmp(self.extraD, other.extraD))

    def _splitnum(self, string):
        match = re.match(r'((?:[+-]?\d+)?)(.*)', string)
        return (int(match.group(1) or 0),
                match.group(2))


class Version(object):

    def __init__(self, version):
        self._version = version
        self.parts = map(VersionPart, version.split('.'))

    def __repr__(self):
        return 'Version(%s)' % repr(self._version)

    def __str__(self):
        return self._version

    def __cmp__(self, other):
        for s_part, o_part in izip_longest(self.parts, other.parts):
            cres = cmp(s_part, o_part)
            if cres:
                return cres
        return 0

    @property
    def is_release(self):
        return bool(re.match(r'^[\d.]+$', self._version))

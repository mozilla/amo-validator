"""
Basic fabfile to setup environment for running tests
"""
import functools
import os

from fabric.api import local

ROOT = os.path.abspath(os.path.dirname(__file__))

os.environ['PYTHONPATH'] = os.pathsep.join([ROOT,
                                            os.path.join(ROOT, 'validator')])

local = functools.partial(local, capture=False)

def test(pdb=False):
    cmd = 'nosetests'

    if pdb:
        cmd += ' --pdb --pdb-failures -s'

    local(cmd)

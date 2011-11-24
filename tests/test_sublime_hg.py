import sys
import os

import mock

sys.path.insert(0, os.path.dirname(__file__))


from sublime_hg import find_hg_root


def test_ThatHgRootIsFoundCorrectly():
    paths = (
        r'C:\No\Luck\Here',
        r'C:\Sometimes\You\Find\What\You\Are\Looking\For',
        r'C:\Come\Get\Some\If\You\Dare',
    ) 
    old_exists = os.path.exists
    os.path.exists = lambda path: path.endswith('Some\.hg')
    results = [find_hg_root(x) for x in paths]
    os.path.exists = old_exists
    assert results == [None, None, 'C:\\Come\\Get\\Some']


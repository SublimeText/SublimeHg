import unittest
import os

from test_runner import tests_state

from shglib import utils


class TestHelpers(unittest.TestCase):
    def sartUp(self):
        # ss = test_runner.test_view.settings.get('packages.sublime_hg.hg_exe')
        pass

    def testPushd(self):
        cwd = os.getcwdu()
        target = os.environ["TEMP"]
        with utils.pushd(target):
            self.assertEqual(os.getcwdu(), target)
        self.assertEqual(os.getcwdu(), cwd)

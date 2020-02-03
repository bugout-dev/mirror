"""
Tests for allrepos crawler and related functionality
"""

import os
import shutil
import tempfile
import unittest

import mirror.github.allrepos as allrepos

class TestOrderedCrawl(unittest.TestCase):
    """
    Tests that allrepos.ordered_crawl behaves as expected
    """
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_ordered_crawl_1(self):
        start_ids = [99, 1, 13]
        files = []
        for i in range(3):
            new_file = os.path.join(self.tempdir, f'{start_ids[i]}.json')
            with open(new_file, 'w'):
                pass
            files.append(new_file)

        ordered_start_ids = sorted(start_ids)
        ordered_results = allrepos.ordered_crawl(self.tempdir)
        for i, rfile in enumerate(ordered_results):
            self.assertEqual(rfile, os.path.join(self.tempdir, f'{ordered_start_ids[i]}.json'))

    def test_ordered_crawl_2(self):
        ordered_results = allrepos.ordered_crawl(self.tempdir)
        self.assertListEqual(ordered_results, [])

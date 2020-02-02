"""
Tests for mirror CLI
"""

import argparse
import unittest

import mirror.cli

class TestGenerateMirrorCLI(unittest.TestCase):
    def setUp(self):
        self.subcommand = 'test-subcommand'

        def subcommand_populator(parser: argparse.ArgumentParser) -> None:
            parser.add_argument('positional_arg')
            parser.add_argument('--opt-a', '-a', required=True)
            parser.add_argument('--opt-b', '-b', required=False)
            parser.add_argument('--opt-c', '-c', action='store_true')

        self.subcommand_populators = {
            self.subcommand: subcommand_populator,
        }

    def test_generate_mirror_cli_1(self):
        parser = mirror.cli.generate_mirror_cli(self.subcommand_populators)
        args = parser.parse_args([self.subcommand, '-a', 'lol', 'rofl'])
        self.assertEqual(args.opt_a, 'lol')
        self.assertIsNone(args.opt_b)
        self.assertFalse(args.opt_c)
        self.assertEqual(args.positional_arg, 'rofl')

    def test_generate_mirror_cli_2(self):
        parser = mirror.cli.generate_mirror_cli(self.subcommand_populators)
        with self.assertRaises(SystemExit):
            args = parser.parse_args([self.subcommand, 'rofl'])

    def test_generate_mirror_cli_3(self):
        parser = mirror.cli.generate_mirror_cli(self.subcommand_populators)
        with self.assertRaises(SystemExit):
            args = parser.parse_args([self.subcommand, '--opt-a', 'lol'])

    def test_generate_mirror_cli_4(self):
        parser = mirror.cli.generate_mirror_cli(self.subcommand_populators)
        args = parser.parse_args([self.subcommand, '--opt-a', 'lol', 'rofl', '--opt-c'])
        self.assertEqual(args.opt_a, 'lol')
        self.assertIsNone(args.opt_b)
        self.assertTrue(args.opt_c)
        self.assertEqual(args.positional_arg, 'rofl')

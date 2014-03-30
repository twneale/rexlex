import re
import unittest

from rexlex import Lexer, ScannerLexer
from rexlex.lexer.itemclass import get_itemclass


class TestableLexer(Lexer):
    """Test tuple state transitions including #pop."""

    LOGLEVEL = None

    re_skip = re.compile('\s+')
    tokendefs = {
        'root': [
            ('Root', 'a', 'bar'),
            ('Root', 'e'),
        ],
        'foo': [
            ('Foo', 'd'),
        ],
        'bar': [
            ('Bar', 'b', 'bar'),
            ('Bar', 'c', 'foo'),
        ],
    }


class TestableScannerLexer(ScannerLexer):
    lexer = TestableLexer

    def get_hooks(self):
        '''Return the primary hook regex for the scan.
        '''
        yield 'a'


class ScannerLexerTest(unittest.TestCase):
    text = 'xabcdexabcdex'
    Item = get_itemclass(text)
    maxDiff = None

    expected = [
        [Item(start=1, end=2, token='Root'),
         Item(start=2, end=3, token='Bar'),
         Item(start=3, end=4, token='Bar'),
         Item(start=4, end=5, token='Foo'),
         Item(start=5, end=6, token='Root')],
        [Item(start=7, end=8, token='Root'),
         Item(start=8, end=9, token='Bar'),
         Item(start=9, end=10, token='Bar'),
         Item(start=10, end=11, token='Foo'),
         Item(start=11, end=12, token='Root')]]

    def test(self):
        toks = list(TestableScannerLexer(self.text))
        self.assertEqual(toks, self.expected)

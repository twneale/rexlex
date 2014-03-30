import re
import unittest

from rexlex import Lexer
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


class TupleTransTest(unittest.TestCase):
    text = 'abcde'
    Item = get_itemclass(text)

    expected = [
        Item(start=0, end=1, token='Root'),
        Item(start=1, end=2, token='Bar'),
        Item(start=2, end=3, token='Bar'),
        Item(start=3, end=4, token='Foo'),
        Item(start=4, end=5, token='Root')]

    def test(self):
        toks = list(TestableLexer(self.text))
        self.assertEqual(toks, self.expected)

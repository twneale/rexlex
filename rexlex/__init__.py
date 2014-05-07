# -*- coding: utf-8 -*-
"""Basic regex lexer implementation"""
# :copyright: (c) 2009 - 2012 Thom Neale and individual contributors,
#                 All rights reserved.
# :license:   BSD (3 Clause), see LICENSE for more details.

from __future__ import absolute_import
import logging.config

from rexlex import config


VERSION = (0, 0, 2, '')
__version__ = '.'.join(str(p) for p in VERSION[0:3]) + ''.join(VERSION[3:])
__author__ = 'Thom Neale'
__contact__ = 'twneale@gmail.com'
__homepage__ = 'http://github.com/twneale/rexlex'
__docformat__ = 'restructuredtext'
__all__ = [
    'Lexer', 'Token', 'include', 'bygroups', 'Rule',
    'ScannerLexer', 'IncompleteLex',
    'TRACE', 'TRACE_RESULT', 'TRACE_META', 'TRACE_STATE',
    'TRACE_RULE', '__version__']


# Configure logging.
logging.config.dictConfig(config.LOGGING_CONFIG)

# Import cumstom log levels.
from rexlex.log_config import (
    REXLEX_TRACE_RESULT as TRACE_RESULT,
    REXLEX_TRACE_META as TRACE_META,
    REXLEX_TRACE_STATE as TRACE_STATE,
    REXLEX_TRACE_RULE as TRACE_RULE,
    REXLEX_TRACE as TRACE,
)

# Import lexer.
from rexlex.lexer.lexer import Lexer
from rexlex.lexer.tokentype import Token
from rexlex.lexer.utils import include, bygroups, Rule
from rexlex.lexer.exceptions import IncompleteLex

# Import Scanner.
from rexlex.scanner.scanner import ScannerLexer


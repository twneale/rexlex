# -*- coding: utf-8 -*-
"""Pythonic parsing framework"""
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
__homepage__ = 'http://twneale.github.io/tater'
__docformat__ = 'restructuredtext'
__all__ = [
    'Lexer', 'Scanner', 'Token', 'include', 'bygroups', 'Rule',
    '__version__']


# rexlex imports.
from rexlex.lexer import Lexer
from rexlex.tokentype import Token
from rexlex.lexer.utils import include, bygroups, rule
from rexlex.lexer.exceptions import IncompleteLex



# Configure logging.
logging.config.dictConfig(config.LOGGING_CONFIG)


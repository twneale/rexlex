import re
import sys
import logging
import functools

from hercules import CachedClassAttr

import rexlex
from rexlex.config import LOG_MSG_MAXWIDTH
from rexlex.lexer import tokendefs
from rexlex.lexer import exceptions
from rexlex.lexer.utils import include, bygroups
from rexlex.lexer.itemclass import get_itemclass
from rexlex.lexer.tokentype import _TokenType
from rexlex.lexer.py2compat import str, unicode, bytes, basestring


class _LogMessages:
    pass


class Lexer(object):
    '''Basic regex lexer with optionally extremely noisy debug/trace output.
    '''
    _log_messages = _msg = _LogMessages()
    _MAXWIDTH = LOG_MSG_MAXWIDTH

    # Lexer exceptions.
    _Finished = exceptions.Finished
    _MatchFound = exceptions.MatchFound
    _IncompleteLex = exceptions.IncompleteLex

    # Custom log functions.
    _logger = logging.getLogger('rexlex')
    trace_result = _logger.rexlex_trace_result
    trace_meta = _logger.rexlex_trace_meta
    trace_state = _logger.rexlex_trace_state
    trace_rule = _logger.rexlex_trace_rule
    trace = _logger.rexlex_trace

    LOGLEVEL = None
    _log_messages = {}

    def __init__(self, text, pos=None, statestack=None, **kwargs):
        '''Text is the input string to lex. Pos is the
        position at which to start, or 0.
        '''
        # Set initial state.
        self.text = text
        self.pos = pos or 0
        self.statestack = statestack or ['root']
        self.Item = get_itemclass(text)

        re_skip = getattr(self, 're_skip', None)
        if re_skip is not None:
            re_skip = re.compile(re_skip).match
        self.re_skip = re_skip

        if hasattr(self, 'DEBUG'):
            if isinstance(self.DEBUG, bool):
                self._logger.setLevel(rexlex.REXLEX_TRACE)
            else:
                self._logger.setLevel(self.DEBUG)
        else:
            self.loglevel = getattr(self, 'loglevel', None)
            if self.loglevel is None:
                self.loglevel = kwargs.get('loglevel', None)
            if self.loglevel is None:
                self._logger.setLevel(10)

    _msg.ITEM = '  %r'

    def __iter__(self):
        self.trace_meta('Tokenizing text: %r', self.text)
        text_len = len(self.text)
        Item = self.Item
        msg = self._msg
        while True:
            if text_len <= self.pos:
                # If here, we hit the end of the input. Stop.
                return
            try:
                for item in self.scan():
                    item = Item(*item)
                    self.trace_result(msg.ITEM,  (item,))
                    yield item
            except self._Finished:
                if text_len <= self.pos:
                    return
                elif getattr(self, 'raise_incomplete', False):
                    raise self._IncompleteLex()
                else:
                    return

    @CachedClassAttr
    def _tokendefs(cls):
        return tokendefs.Compiler(cls).compile_all()

    _msg.SCAN_TEXT = '  scan: %r'
    _msg.SCAN_POS = '  scan: pos = %r'
    _msg.SCAN_STATE = '  scan: state is %r'
    _msg.SCAN_ROOTSTATE = "  scan: state is 'root'"
    _msg.SCAN_MATCH_FOUND = '  _scan: match found--returning.'
    _msg.SCAN_POPPING = '  scan: match not found. Popping from %r.'
    _msg.SCAN_STATES_EXHAUSTED = 'All out of states to process. Stopping.'
    _msg.SCAN_POPPING_ROOT = '  scan: popping from root state; stopping.'

    def scan(self):
        msg = self._msg
        self.trace_meta(msg.SCAN_TEXT, self.text[self.pos:(self.pos + self._MAXWIDTH)])
        self.trace_meta(msg.SCAN_POS, self.pos)

        try:
            defs = self._tokendefs[self.statestack[-1]]
            self.trace_state(msg.SCAN_STATE, self.statestack[-1])
        except IndexError:
            defs = self._tokendefs['root']
            self.trace_state(msg.SCAN_ROOTSTATE)

        dont_emit = getattr(self, 'dont_emit', [])
        try:
            for start, end, token in self._process_state(defs):
                if token in dont_emit:
                    pass
                else:
                    yield start, end, token
        except self._MatchFound:
            self.trace(msg.SCAN_MATCH_FOUND)
            return

        self.trace_state(msg.SCAN_POPPING, self.statestack)
        try:
            self.statestack.pop()
        except IndexError:
            self.trace_meta(msg.SCAN_STATES_EXHAUSTED)
            raise self._Finished()

        if not self.statestack:
            self.trace_state(msg.SCAN_POPPING_ROOT)
            # We popped from the root state.
            raise self._Finished()

    _msg.STATE_STARTING = ' _process_state: starting state %r'
    _msg.STATE_STACK = ' _process_state: stack: %r'

    def _process_state(self, defs):
        msg = self._msg
        if self.statestack:
            self.trace_meta(msg.STATE_STARTING, self.statestack[-1])
            self.trace_state(msg.STATE_STACK, self.statestack)
        for rule in defs:
            for item in self._process_rule(rule):
                yield item

    _msg.PROCESS_RULE_SKIPPED = '  _process_rule: skipped %r'
    _msg.PROCESS_RULE_ADVANCING = '  _process_rule: advancing pos from %r to %r'
    _msg.PROCESS_RULE_STATESTACK = '  _process_rule: statestack: %r'
    _msg.PROCESS_RULE_TRYING_REGEX = '  _process_rule: trying regex %r'
    _msg.PROCESS_RULE_MATCH_FOUND = '  _process_rule: match found: %s'
    _msg.PROCESS_RULE_MATCHED_PATTERN = '  _process_rule: matched pattern: %r'
    _msg.PROCESS_RULE_MATCH_LENGTH = '  _process_rule: %r has length %r'

    def _process_rule(self, rule):
        msg = self._msg
        token, rgxs, push, pop, swap = rule
        pos_changed = False
        if self.re_skip:
            # Skipper.
            # Try matching the regexes before stripping,
            # in case they specify leading strippables.
            m = self.re_skip(self.text, self.pos)
            if m:
                self.trace_rule(msg.PROCESS_RULE_SKIPPED, m.group())
                self.trace_rule(msg.PROCESS_RULE_ADVANCING, self.pos, m.end())
                pos_changed = True
                self.pos = m.end()

        PROCESS_RULE_STATESTACK = self._msg.PROCESS_RULE_STATESTACK
        PROCESS_RULE_TRYING_REGEX = self._msg.PROCESS_RULE_TRYING_REGEX
        PROCESS_RULE_MATCH_FOUND = self._msg.PROCESS_RULE_MATCH_FOUND
        PROCESS_RULE_MATCHED_PATTERN = self._msg.PROCESS_RULE_MATCHED_PATTERN
        PROCESS_RULE_MATCH_LENGTH = self._msg.PROCESS_RULE_MATCH_LENGTH
        PROCESS_RULE_ADVANCING = self._msg.PROCESS_RULE_ADVANCING

        for rgx in rgxs:
            self.trace_rule(PROCESS_RULE_STATESTACK, self.statestack)
            m = rgx.match(self.text, self.pos)
            self.trace(PROCESS_RULE_TRYING_REGEX, rgx.pattern)
            if m:
                self.trace_rule(PROCESS_RULE_MATCH_FOUND, m.group())
                self.trace_rule(PROCESS_RULE_MATCHED_PATTERN, rgx.pattern)
                if isinstance(token, (_TokenType, basestring)):
                    start, end = m.span()
                    yield start, end, token
                else:
                    matched = m.group()
                    for token, text in zip(token, m.groups()):
                        pos = self.pos + matched.index(text)
                        yield pos, pos + len(text), token

                msg = PROCESS_RULE_MATCH_LENGTH
                self.trace_rule(msg, m.group(), len(m.group()))
                msg = PROCESS_RULE_ADVANCING
                self.trace_rule(msg, self.pos, m.end())
                self.pos = m.end()
                self._update_state(rule)
                raise self._MatchFound()

    _msg.UPDATE_SWAPPING = '  _update_state: swapping current state for %r'
    _msg.UPDATE_POPPED = '  _update_state: popped %r'
    _msg.UPDATE_POPPED_MULTI = '  _update_state: popping %r states'
    _msg.UPDATE_POP_ALL = '  _update_state: popping all %r'
    _msg.UPDATE_PUSH = '  _update_state: pushing %r'
    _msg.UPDATE_PUSH_ALL = '  _update_state: pushing all %r'

    def _update_state(self, rule):
        msg = self._msg
        token, rgxs, push, pop, swap = rule
        statestack = self.statestack

        # State transition
        if swap and not (push or pop):
            msg = self._msg.UPDATE_SWAPPING
            self.trace_state(msg, statestack[-1])
            statestack.pop()
            statestack.append(swap)
        else:
            if pop:
                if isinstance(pop, bool):
                    popped = statestack.pop()
                    self.trace_state(msg.UPDATE_POPPED, popped)
                elif isinstance(pop, int):
                    self.trace_state(msg.UPDATE_POPPED_MULTI, pop)
                    for i in range(pop):
                        popped = statestack.pop()
                        self.trace_state(msg.UPDATE_POPPED, popped)

                # If it's a set, pop all that match.
                elif isinstance(pop, set):
                    self.trace_state(msg.UPDATE_POP_ALL, pop)
                    while statestack[-1] in pop:
                        popped = statestack.pop()
                        self.trace_state(msg.UPDATE_POPPED, (popped))

            if push:
                self.trace_state(msg.UPDATE_PUSH, (push,))
                if isinstance(push, basestring):
                    if push == '#pop':
                        statestack.pop()
                    elif push.startswith('#pop:'):
                        numpop = push.replace('#pop:', '')
                        for i in range(numpop):
                            statestack.pop()
                    else:
                        statestack.append(push)
                else:
                    self.trace_state(msg.UPDATE_PUSH_ALL, (push,))
                    for state in push:
                        self.trace_state(msg.UPDATE_PUSH, state)
                        statestack.append(state)

import re
import sys
import logging
import functools

from hercules import CachedClassAttr

from rexlex.config import LOG_MSG_MAXWIDTH
from rexlex.tokentype import _TokenType

from rexlex.lexer import tokendefs
from rexlex.lexer import exceptions
from rexlex.lexer.utils import include, bygroups
from rexlex.lexer.itemclass import get_itemclass


class Lexer(object):
    '''Basic regex lexer with optionally extremely noisy debug/trace output.
    '''
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

    def __init__(self, text, pos=None, statestack=None, **kwargs):
        '''Text is the input string to lex. Pos is the
        position at which to start, or 0.
        '''
        # Set initial state.
        self.text = text
        self.pos = pos or 0
        self.statestack = statestack or []
        self.Item = get_itemclass(text)

        if self.re_skip is not None:
            self.re_skip = re.compile(self.re_skip).match

    def __iter__(self):
        self.trace_meta('Tokenizing text: %r' % self.text)
        text_len = len(self.text)
        Item = self.Item
        while True:
            if text_len <= self.pos:
                # If here, we hit the end of the input. Stop.
                return
            try:
                for item in self.scan():
                    item = Item(*item)
                    self.trace_result('  %r' % (item,))
                    yield item
            except self.Finished:
                if text_len <= self.pos:
                    return
                elif self.raise_incomplete:
                    raise self._IncompleteLex()
                else:
                    return

    @CachedClassAttr
    def _tokendefs(self):
        return tokendefs.Compiler(cls).compile_all()

    def scan(self):
        self.trace_meta('  scan: %r' % self.text[self.pos:])
        self.trace_meta('  scan: pos = %r' % self.pos)

        try:
            defs = self._tokendefs[self.statestack[-1]]
            self.trace_state('  scan: state is %r' % self.statestack[-1])
        except IndexError:
            defs = self._tokendefs['root']
            self.trace_state("  scan: state is 'root'")

        dont_emit = getattr(self, 'dont_emit', [])
        try:
            for start, end, token in self._process_state(defs):
                if token in dont_emit:
                    pass
                else:
                    yield start, end, token
        except self._MatchFound:
            self.trace('  _scan: match found--returning.')
            return

        msg = '  scan: match not found. Popping from %r.'
        self.trace_state(msg % self.statestack)
        try:
            self.statestack.pop()
        except IndexError:
            self.trace_meta('All out of states to process.Stopping.')
            raise self._Finished()

        if not self.statestack:
            self.trace_state('  scan: popping from root state; stopping.')
            # We popped from the root state.
            raise self._Finished()

        # # Advance 1 chr if we tried all the states on the stack.
        # if not self.statestack:
        #     self.info('  scan: advancing 1 char.')
        #     self.pos += 1

    def _process_state(self, defs):
        if self.statestack:
            msg = ' _process_state: starting state %r'
            self.trace_meta(msg % self.statestack[-1])
            msg = ' _process_state: stack: %r'
            self.trace_state(msg % self.statestack)
        for rule in defs:
            self.debug(' _process_state: starting rule %r' % (rule,))
            for item in self._process_rule(rule):
                yield item

    def _process_rule(self, rule):
        token, rgxs, push, pop, swap = rule

        pos_changed = False
        if self.re_skip:
            # Skipper.
            # Try matching the regexes before stripping,
            # in case they specify leading strippables.
            m = self.re_skip(self.text, self.pos)
            if m:
                self.trace_rule('  _process_rule: skipped %r' % m.group())
                msg = '  _process_rule: advancing pos from %r to %r'
                self.trace_rule(msg % (self.pos, m.end()))
                pos_changed = True
                self.pos = m.end()

        for rgx in rgxs:
            self.trace_rule('  _process_rule: statestack: %r' % self.statestack)
            if pos_changed:
                self.trace_rule('  _process_rule:        ' + (' ' * self.pos) + '^')
                pos_changed = False

            m = rgx.match(self.text, self.pos)
            self.trace('  _process_rule: trying regex %r' % rgx.pattern)
            if m:
                self.trace_rule('  _process_rule: match found: %s' % m.group())
                self.trace_rule('  _process_rule: matched pattern: %r' % rgx.pattern)
                if isinstance(token, (_TokenType, basestring)):
                    start, end = m.span()
                    yield start, end, token
                else:
                    matched = m.group()
                    for token, text in zip(token, m.groups()):
                        pos = self.pos + matched.index(text)
                        yield pos, pos + len(text), token

                msg = '  _process_rule: %r has length %r'
                self.trace_rule(msg % (m.group(), len(m.group())))
                msg = '  _process_rule: advancing pos from %r to %r'
                self.trace_rule(msg % (self.pos, m.end()))
                self.pos = m.end()
                self._update_state(rule)
                raise self._MatchFound()

    def _update_state(self, rule):
        token, rgxs, push, pop, swap = rule
        statestack = self.statestack

        # State transition
        if swap and not (push or pop):
            msg = '  _update_state: swapping current state for %r'
            self.trace_state(msg % statestack[-1])
            statestack.pop()
            statestack.append(swap)
        else:
            if pop:
                if isinstance(pop, bool):
                    popped = statestack.pop()
                    self.trace_state('  _update_state: popped %r' % popped)
                elif isinstance(pop, int):
                    self.trace_state('  _update_state: popping %r states' % pop)
                    msg = '    _update_state: [%r] popped %r'
                    for i in range(pop):
                        popped = statestack.pop()
                        self.trace_state(msg % (i, popped))

                # If it's a set, pop all that match.
                elif isinstance(pop, set):
                    self.trace_state('  _update_state: popping all %r' % pop)
                    msg = '    _update_state: popped %r'
                    while statestack[-1] in pop:
                        popped = statestack.pop()
                        self.trace_state(msg % (popped))

            if push:
                self.info('  _update_state: pushing %r' % (push,))
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
                    self.trace_state('  _update_state: pushing all %r' % (push,))
                    msg = '    _update_state: pushing %r'
                    for state in push:
                        self.trace_state(msg % state)
                        statestack.append(state)




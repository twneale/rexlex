import re
import sys
import logging
import functools

from hercules import CachedClassAttr

from tater.core.config import LOG_MSG_MAXWIDTH
from tater.core.tokentype import _TokenType

from tater.base.lexer import tokendefs
from tater.base.lexer.utils import include, bygroups, Rule
from tater.base.lexer.itemclass import get_itemclass
from tater.base.lexer.exceptions import IncompleteLex



__all__ = [
    'Lexer', 'DebugLexer', 'include', 'bygroups',
    'Rule', 'IncompleteLex']


class LexerBase(object):
    '''Basic regex Lexer.
    '''

    def __init__(self, text, **kwargs):
        '''Text is the input string to lex. Pos is the
        position at which to start, or 0.
        '''
        pos = 0
        statestack = ['root']
        self.text = text

        names = (
            're_skip',
            'raise_incomplete',
            'dont_emit')
        for name in names:
            value = kwargs.get(name, getattr(self, name))
            setattr(self, name, value)

    def __iter__(self):
        return self.lex()

    @CachedClassAttr
    def _tokendefs(self):
        return tokendefs.Compiler(cls).compile_all()

    @CachedAttr
    def _item_cls(self):
        return get_itemclass(self.text)

    def lex(self):
        pos = self.pos
        text = self.text
        statestack = self.statestack or ['root']
        tokendefs = self._tokendefs
        re_skip = self.re_skip
        text_len = len(text)
        dont_emit = self.dont_emit or []
        raise_incomplete = self.raise_incomplete

        if re_skip is not None:
            re_skip = re.compile(re_skip).match



class _DebugLexerBase(_LexerBase):
    '''Extremely noisy debug version of the basic lexer.
    '''
    __metaclass__ = DebugLexerMeta

    class _Finished(Exception):
        pass

    class _MatchFound(Exception):
        pass

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
        self.info('Tokenizing text: %r' % self.text)
        text_len = len(self.text)
        Item = self.Item
        while True:
            if text_len <= self.pos:
                # If here, we hit the end of the input. Stop.
                return
            try:
                for item in self.scan():
                    item = Item(*item)
                    self.warn('  %r' % (item,))
                    yield item
            except self._Finished:
                if text_len <= self.pos:
                    return
                elif self.raise_incomplete:
                    raise IncompleteLex()
                else:
                    return

    def scan(self):
        # Get the tokendefs for the current state.
        # self.warn('  scan: text: %s' % self.text)
        # self.warn('  scan:        ' + (' ' * self.pos) + '^')
        self.warn('  scan: %r' % self.text[self.pos:])
        self.warn('  scan: pos = %r' % self.pos)

        try:
            defs = self._tokendefs[self.statestack[-1]]
            self.info('  scan: state is %r' % self.statestack[-1])
        except IndexError:
            defs = self._tokendefs['root']
            self.info("  scan: state is 'root'")

        dont_emit = getattr(self, 'dont_emit', [])
        try:
            for start, end, token in self._process_state(defs):
                if token in dont_emit:
                    pass
                else:
                    yield start, end, token
        except self._MatchFound:
            self.debug('  _scan: match found--returning.')
            return

        msg = '  scan: match not found. Popping from %r.'
        self.info(msg % self.statestack)
        try:
            self.statestack.pop()
        except IndexError:
            self.debug('All out of states to process.Stopping.')
            raise self._Finished()

        if not self.statestack:
            self.debug('  scan: popping from root state; stopping.')
            # We popped from the root state.
            raise self._Finished()

        # # Advance 1 chr if we tried all the states on the stack.
        # if not self.statestack:
        #     self.info('  scan: advancing 1 char.')
        #     self.pos += 1

    def _process_state(self, defs):
        if self.statestack:
            msg = ' _process_state: starting state %r'
            self.critical(msg % self.statestack[-1])
            msg = ' _process_state: stack: %r'
            self.warn(msg % self.statestack)
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
                self.info('  _process_rule: skipped %r' % m.group())
                msg = '  _process_rule: advancing pos from %r to %r'
                self.info(msg % (self.pos, m.end()))
                pos_changed = True
                self.pos = m.end()

        for rgx in rgxs:
            self.debug('  _process_rule: statestack: %r' % self.statestack)
            if pos_changed:
                self.info('  _process_rule:        ' + (' ' * self.pos) + '^')
                pos_changed = False

            m = rgx.match(self.text, self.pos)
            self.debug('  _process_rule: trying regex %r' % rgx.pattern)
            if m:
                self.info('  _process_rule: match found: %s' % m.group())
                self.info('  _process_rule: matched pattern: %r' % rgx.pattern)
                if isinstance(token, (_TokenType, basestring)):
                    start, end = m.span()
                    yield start, end, token
                else:
                    matched = m.group()
                    for token, text in zip(token, m.groups()):
                        pos = self.pos + matched.index(text)
                        yield pos, pos + len(text), token

                msg = '  _process_rule: %r has length %r'
                self.info(msg % (m.group(), len(m.group())))
                msg = '  _process_rule: advancing pos from %r to %r'
                self.info(msg % (self.pos, m.end()))
                self.pos = m.end()
                self._update_state(rule)
                raise self._MatchFound()

    def _update_state(self, rule):
        token, rgxs, push, pop, swap = rule
        statestack = self.statestack

        # State transition
        if swap and not (push or pop):
            msg = '  _update_state: swapping current state for %r'
            self.info(msg % statestack[-1])
            statestack.pop()
            statestack.append(swap)
        else:
            if pop:
                if isinstance(pop, bool):
                    popped = statestack.pop()
                    self.info('  _update_state: popped %r' % popped)
                elif isinstance(pop, int):
                    self.info('  _update_state: popping %r states' % pop)
                    msg = '    _update_state: [%r] popped %r'
                    for i in range(pop):
                        popped = statestack.pop()
                        self.info(msg % (i, popped))

                # If it's a set, pop all that match.
                elif isinstance(pop, set):
                    self.info('  _update_state: popping all %r' % pop)
                    msg = '    _update_state: popped %r'
                    while statestack[-1] in pop:
                        popped = statestack.pop()
                        self.info(msg % (popped))

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
                    self.info('  _update_state: pushing all %r' % (push,))
                    msg = '    _update_state: pushing %r'
                    for state in push:
                        self.info(msg % state)
                        statestack.append(state)




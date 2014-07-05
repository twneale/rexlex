'''
class Scanner(BaseScanner):
    lexer = Lexer

    def get_hooks(self):
        database_ids = map(methodcaller('upper'), settings.DATABASE_IDS)
        for rgx in regexes + database_ids:
            yield '\d+\s+' + rgx

            # R. v. Brezack, [1949] O.R. 888, [1950] 2 D.L.R. 265,
            yield '[\(\[]\d{4}[\)\]],?\s+' + rgx
            yield '[\(\[]\d{4}[\)\]],?\s+\d+\s+' + rgx

            # [1861-73] All E.R. Rep. 157
            yield '[\(\[]\d+\S+?[\)\]],?\s+' + rgx

    def get_startnode(self, matchobj):
        return get_startnode()

    def handle_parse_error(self, start_node, exc):
        start_node.getroot().pprint()
        raise exc
'''

import re
from operator import methodcaller

from rexlex import IncompleteLex


__all__ = ["Scanner"]


class ScannerContinue:
    '''Continue in scanner's loop.
    '''

class ScannerLexer(object):
    '''This object tries uses the hook functions defined
    in get_hooks to find points within the input string
    at which to begin lexing with the provided lexer.
    The resulting token streams are resolved against the
    object provided by get_startnode. Iterating over
    the instance yields a sequence of parse trees.
    '''
    hooks = None
    lexer = None
    debug = False

    # If true, begin lexing after the end index of the
    # scanner match objects.
    skip_match = False

    Continue = ScannerContinue

    def get_hooks(self):
        '''Yields a regex used to find positions in the input string
        to begin lexing from.
        '''
        raise NotImplementedError()

    def get_startnode(self, matchobj):
        '''Get a node to start at. Called once per items.
        '''
        raise NotImplementedError()

    def __init__(self, text, pos=0, lexer=None):
        self.text = text
        self.pos = pos
        self.lexer = self.lexer or lexer
        if hasattr(self.lexer, 'raise_incomplete'):
            self.lexer.raise_incomplete = False
        self.hooks = self.hooks or list(self.get_hooks())

    def __iter__(self):
        '''Yield parse trees.
        '''
        for matchobj in self.matches_ordered():
            if not self.check_matchobj(matchobj):
                continue
            items = list(self.get_tokens(matchobj))
            if items is None:
                continue
            try:
                start, end = self.get_span(items)
            except self.Continue():
                continue
            self.pos = end
            yield items

    def check_matchobj(self, matchobj):
        if self.pos <= matchobj.start():
            # This match
            self.pos = matchobj.start()
            return True
        else:
            # This match occurred within previous text.
            return False

    def iter_matches(self):
        for hook in self.hooks:
            for matchobj in re.finditer(hook, self.text):
                yield matchobj

    def matches_ordered(self):
        return sorted(self.iter_matches(), key=methodcaller('start'))

    def get_span(self, tokens):
        return tokens[0].start, tokens[-1].end

    def handle_parse_error(self, start_node, exc):
        raise exc

    def get_tokens(self, matchobj):
        if self.skip_match:
            start_pos = matchobj.end()
        else:
            start_pos = self.pos
        try:
            items = self.lexer(self.text, pos=start_pos)
        except IncomepleteLex as exc:
            self.handle_parse_error(start, exc)

        return items


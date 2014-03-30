
class IncompleteLex(Exception):
    '''Raised if the lexer couldn't consume all the input.
    '''


class BogusIncludeError(Exception):
    '''Raised if the lexer tries to ``include`` a nonexistent state.
    '''


class ConfigurationError(Exception):
    '''Raised is lexer is misconfigured.
    '''


class Finished(Exception):
    '''Raise when lexer reaches the end of input.
    '''


class MatchFound(Exception):
    '''Breaks the lexer loop when a match is found.
    '''

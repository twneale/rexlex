'''
Establish custom log levels for rexlexer's verbose output.
'''
import logging
from .config import LOG_MSG_MAXWIDTH


# ---------------------------------------------------------------------------
# Establish custom log levels.
# ---------------------------------------------------------------------------

# Used to report tokens getting yielded.
REXLEX_TRACE_RESULT = 9

# Used to report starting, stopping, etc.
REXLEX_TRACE_META = 8

# Used to report changes to lexer state.
REXLEX_TRACE_STATE = 7

# Used to report on specific rules.
REXLEX_TRACE_RULE = 6

# Used to dump as much info as possible.
REXLEX_TRACE = 5


REXLEX_LOG_LEVELS = (
    (REXLEX_TRACE_RESULT, 'REXLEX_TRACE_RESULT', 'rexlex_trace_result'),
    (REXLEX_TRACE_META, 'REXLEX_TRACE_META', 'rexlex_trace_meta'),
    (REXLEX_TRACE_STATE, 'REXLEX_TRACE_STATE', 'rexlex_trace_state'),
    (REXLEX_TRACE_RULE, 'REXLEX_TRACE_RULE', 'rexlex_trace_rule'),
    (REXLEX_TRACE, 'REXLEX_TRACE', 'rexlex_trace'),
)
for loglevel, loglevel_name, method_name in REXLEX_LOG_LEVELS:
    logging.addLevelName(loglevel, loglevel_name)


def rexlex_trace_result(self, message, *args, **kws):
    if self.isEnabledFor(REXLEX_TRACE_RESULT):
        self._log(REXLEX_TRACE_RESULT, message, args, **kws)
setattr(logging.Logger, 'rexlex_trace_result', rexlex_trace_result)

def rexlex_trace_meta(self, message, *args, **kws):
    if self.isEnabledFor(REXLEX_TRACE_META):
        self._log(REXLEX_TRACE_META, message, args, **kws)
setattr(logging.Logger, 'rexlex_trace_meta', rexlex_trace_meta)

def rexlex_trace_state(self, message, *args, **kws):
    if self.isEnabledFor(REXLEX_TRACE_STATE):
        self._log(REXLEX_TRACE_STATE, message, args, **kws)
setattr(logging.Logger, 'rexlex_trace_state', rexlex_trace_state)

def rexlex_trace_rule(self, message, *args, **kws):
    if self.isEnabledFor(REXLEX_TRACE_RULE):
        self._log(REXLEX_TRACE_RULE, message, args, **kws)
setattr(logging.Logger, 'rexlex_trace_rule', rexlex_trace_rule)

def rexlex_trace(self, message, *args, **kws):
    if self.isEnabledFor(REXLEX_TRACE):
        self._log(REXLEX_TRACE, message, args, **kws)
setattr(logging.Logger, 'rexlex_trace', rexlex_trace)


# ---------------------------------------------------------------------------
# Colorize them.
# ---------------------------------------------------------------------------

#
# Copyright (C) 2010-2012 Vinay Sajip. All rights reserved.
# Licensed under the new BSD license.
#
import ctypes
import logging
import os


class ColorizingStreamHandler(logging.StreamHandler):
    # color names to indices
    color_map = {
        'black': 0,
        'red': 1,
        'green': 2,
        'yellow': 3,
        'blue': 4,
        'magenta': 5,
        'cyan': 6,
        'white': 7,
    }

    #levels to (background, foreground, bold/intense)
    if os.name == 'nt':
        level_map = {
            REXLEX_TRACE: (None, 'blue', True),
            REXLEX_TRACE_RULE: (None, 'white', False),
            REXLEX_TRACE_STATE: (None, 'yellow', True),
            REXLEX_TRACE_META: (None, 'red', True),
            REXLEX_TRACE_RESULT: ('red', 'white', True),
        }
    else:
        level_map = {
            REXLEX_TRACE: (None, 'blue', False),
            REXLEX_TRACE_RULE: (None, 'white', False),
            REXLEX_TRACE_STATE: (None, 'yellow', False),
            REXLEX_TRACE_META: (None, 'red', False),
            REXLEX_TRACE_RESULT: ('red', 'white', True),
        }
    csi = '\x1b['
    reset = '\x1b[0m'

    @property
    def is_tty(self):
        # bluff for Jenkins
        if os.environ.get('JENKINS_URL'):
            return True
        isatty = getattr(self.stream, 'isatty', None)
        return isatty and isatty()

    def emit(self, record):
        try:
            message = self.format(record)
            stream = self.stream
            if not self.is_tty:
                stream.write(message)
            else:
                self.output_colorized(message)
            stream.write(getattr(self, 'terminator', '\n'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

    if os.name != 'nt':
        def output_colorized(self, message):    # NOQA
            self.stream.write(message)
    else:
        import re
        ansi_esc = re.compile(r'\x1b\[((?:\d+)(?:;(?:\d+))*)m')

        nt_color_map = {
            0: 0x00,    # black
            1: 0x04,    # red
            2: 0x02,    # green
            3: 0x06,    # yellow
            4: 0x01,    # blue
            5: 0x05,    # magenta
            6: 0x03,    # cyan
            7: 0x07,    # white
        }

        def output_colorized(self, message):            # NOQA
            parts = self.ansi_esc.split(message)
            write = self.stream.write
            h = None
            fd = getattr(self.stream, 'fileno', None)
            if fd is not None:
                fd = fd()
                if fd in (1, 2):    # stdout or stderr
                    h = ctypes.windll.kernel32.GetStdHandle(-10 - fd)
            while parts:
                text = parts.pop(0)
                if text:
                    write(text)
                if parts:
                    params = parts.pop(0)
                    if h is not None:
                        params = [int(p) for p in params.split(';')]
                        color = 0
                        for p in params:
                            if 40 <= p <= 47:
                                color |= self.nt_color_map[p - 40] << 4
                            elif 30 <= p <= 37:
                                color |= self.nt_color_map[p - 30]
                            elif p == 1:
                                color |= 0x08   # foreground intensity on
                            elif p == 0:        # reset to default color
                                color = 0x07
                            else:
                                pass     # error condition ignored
                        ctypes.windll.kernel32.SetConsoleTextAttribute(h,
                                                                       color)

    def colorize(self, message, record):
        if record.levelno in self.level_map:
            bg, fg, bold = self.level_map[record.levelno]
            params = []
            if bg in self.color_map:
                params.append(str(self.color_map[bg] + 40))
            if fg in self.color_map:
                params.append(str(self.color_map[fg] + 30))
            if bold:
                params.append('1')
            if params:
                message = ''.join((self.csi, ';'.join(params),
                                   'm', message, self.reset))
        return message

    def format(self, record):
        message = logging.StreamHandler.format(self, record)
        if self.is_tty:
            # Don't colorize any traceback
            parts = message.split('\n', 1)
            parts[0] = self.colorize(parts[0], record)
            message = '\n'.join(parts)
        return message

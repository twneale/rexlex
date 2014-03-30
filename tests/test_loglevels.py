'''Make sure custom logging levels work the way they are supposed to,
since if they don't the logging output of every program that invokes
rexlex will be thoroughly despoiled with by its noisy trace output.
'''
import sys
import logging
import unittest

from six import StringIO
import rexlex.log_config


logger = logging.getLogger('rexlex')


class TestRexlexTraceResult(unittest.TestCase):

    expected = 'rexlex: test'

    def setUp(self):
        self.stderr = StringIO()
        self.real_stderr = sys.stderr
        logger.handlers[0].stream = self.stderr
        logger.setLevel(rexlex.log_config.REXLEX_TRACE_RESULT)

    def tearDown(self):
        logger.handlers[0].stream = self.real_stderr

    def test_trace_result(self):
        logger.rexlex_trace_result("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace_meta("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())

    def test_trace_state(self):
        logger.rexlex_trace_state("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())

    def test_trace_rule(self):
        logger.rexlex_trace_rule("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())


class TestRexlexTraceMeta(unittest.TestCase):

    expected = 'rexlex: test'

    def setUp(self):
        self.stderr = StringIO()
        self.real_stderr = sys.stderr
        logger.handlers[0].stream = self.stderr
        logger.setLevel(rexlex.log_config.REXLEX_TRACE_META)

    def tearDown(self):
        logger.handlers[0].stream = self.real_stderr

    def test_trace_result(self):
        logger.rexlex_trace_result("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace_meta("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_state(self):
        logger.rexlex_trace_state("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())

    def test_trace_rule(self):
        logger.rexlex_trace_rule("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())


class TestRexlexTraceState(unittest.TestCase):

    expected = 'rexlex: test'

    def setUp(self):
        self.stderr = StringIO()
        self.real_stderr = sys.stderr
        logger.handlers[0].stream = self.stderr
        logger.setLevel(rexlex.log_config.REXLEX_TRACE_STATE)

    def tearDown(self):
        logger.handlers[0].stream = self.real_stderr

    def test_trace_result(self):
        logger.rexlex_trace_result("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace_meta("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_state(self):
        logger.rexlex_trace_state("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_rule(self):
        logger.rexlex_trace_rule("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())

    def test_trace(self):
        logger.rexlex_trace("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())


class TestRexlexTraceRule(unittest.TestCase):

    expected = 'rexlex: test'

    def setUp(self):
        self.stderr = StringIO()
        self.real_stderr = sys.stderr
        logger.handlers[0].stream = self.stderr
        logger.setLevel(rexlex.log_config.REXLEX_TRACE_RULE)

    def tearDown(self):
        logger.handlers[0].stream = self.real_stderr

    def test_trace_result(self):
        logger.rexlex_trace_result("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace_meta("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_state(self):
        logger.rexlex_trace_state("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_rule(self):
        logger.rexlex_trace_rule("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace(self):
        logger.rexlex_trace("test")
        self.assertNotIn(self.expected, self.stderr.getvalue())


class TestRexlexTraceResult(unittest.TestCase):

    expected = 'rexlex: test'

    def setUp(self):
        self.stderr = StringIO()
        self.real_stderr = sys.stderr
        logger.handlers[0].stream = self.stderr
        logger.setLevel(rexlex.log_config.REXLEX_TRACE)

    def tearDown(self):
        logger.handlers[0].stream = self.real_stderr

    def test_trace_result(self):
        logger.rexlex_trace_result("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_meta(self):
        logger.rexlex_trace_meta("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_state(self):
        logger.rexlex_trace_state("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace_rule(self):
        logger.rexlex_trace_rule("test")
        self.assertIn(self.expected, self.stderr.getvalue())

    def test_trace(self):
        logger.rexlex_trace("test")
        self.assertIn(self.expected, self.stderr.getvalue())

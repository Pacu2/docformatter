#!/usr/bin/env python

"""Test suite for docformatter."""

import contextlib
import io
import tempfile

try:
    # Python 2.6
    import unittest2 as unittest
except ImportError:
    import unittest

import docformatter


try:
    unicode
except NameError:
    unicode = str


class TestUnits(unittest.TestCase):

    def test_strip_docstring(self):
        self.assertEqual(
            'Hello.',
            docformatter.strip_docstring('''
    """Hello.

    """

    '''))

    def test_strip_docstring_with_single_quotes(self):
        self.assertEqual(
            'Hello.',
            docformatter.strip_docstring("""
    '''Hello.

    '''

    """))

    def test_strip_docstring_with_empty_string(self):
        self.assertEqual('', docformatter.strip_docstring('""""""'))

    def test_format_docstring(self):
        self.assertEqual('"""Hello."""',
                         docformatter.format_docstring('    ', '''
"""

Hello.
"""
'''.strip()))

    def test_format_docstring_with_summary_that_ends_in_quote(self):
        self.assertEqual('''""""Hello"."""''',
                         docformatter.format_docstring('    ', '''
"""

"Hello"
"""
'''.strip()))

    def test_format_docstring_with_bad_indentation(self):
        self.assertEqual('''"""Hello.

    This should be indented but it is not. The
    next line should be indented too. But
    this is okay.

    """''',
                         docformatter.format_docstring('    ', '''
"""Hello.

This should be indented but it is not. The
next line should be indented too. But
    this is okay.
    """
'''.strip()))

    def test_format_docstring_with_trailing_whitespace(self):
        self.assertEqual('''"""Hello.

    This should be not have trailing whitespace. The
    next line should not have trailing whitespace either.

    """''',
                         docformatter.format_docstring('    ', '''
"""Hello.\t
\t
    This should be not have trailing whitespace. The\t\t\t
    next line should not have trailing whitespace either.\t
\t
    """
'''.strip()))

    def test_format_docstring_with_no_post_description_blank(self):
        self.assertEqual('''"""Hello.

    Description.
    """''',
                         docformatter.format_docstring('    ', '''
"""

Hello.

    Description.


    """
'''.strip(), post_description_blank=False))

    def test_format_docstring_with_pre_summary_newline(self):
        self.assertEqual('''"""
    Hello.

    Description.

    """''',
                         docformatter.format_docstring('    ', '''
"""

Hello.

    Description.


    """
'''.strip(), pre_summary_newline=True))

    def test_format_docstring_with_empty_docstring(self):
        self.assertEqual('""""""',
                         docformatter.format_docstring('    ', '""""""'))

    def test_format_docstring_with_no_period(self):
        self.assertEqual('"""Hello."""',
                         docformatter.format_docstring('    ', '''
"""

Hello
"""
'''.strip()))

    def test_format_docstring_with_single_quotes(self):
        self.assertEqual('"""Hello."""',
                         docformatter.format_docstring('    ', """
'''

Hello.
'''
""".strip()))

    def test_format_docstring_with_single_quotes_multiline(self):
        self.assertEqual('''
    """Return x factorial.

    This uses math.factorial.

    """
'''.strip(),
            docformatter.format_docstring('    ', """
    '''
    Return x factorial.

    This uses math.factorial.
    '''
""".strip()))

    def test_format_docstring_with_wrap(self):
        min_line_length = 30
        for max_length in range(min_line_length, 100):
            for num_indents in range(0, 20):
                indentation = ' ' * num_indents
                formatted_text = indentation + docformatter.format_docstring(
                    indentation=indentation,
                    docstring=generate_random_docstring(
                        max_word_length=min_line_length // 2),
                    summary_wrap_length=max_length)

                for line in formatted_text.split('\n'):
                    # It is not the formatter's fault if a word is too long to
                    # wrap.
                    if len(line.split()) > 1:
                        self.assertLessEqual(len(line), max_length)

    def test_format_code(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo."""
''',
            docformatter.format_code(
                unicode('''\
def foo():
    """
    Hello foo.
    """
''')))

    def test_format_code_with_empty_string(self):
        self.assertEqual(
            '',
            docformatter.format_code(''))

    def test_format_code_with_tabs(self):
        self.assertEqual(
            '''\
def foo():
\t"""Hello foo."""
\tif True:
\t\tx = 1
''',
            docformatter.format_code(
                unicode('''\
def foo():
\t"""
\tHello foo.
\t"""
\tif True:
\t\tx = 1
''')))

    def test_format_code_with_mixed_tabs(self):
        self.assertEqual(
            '''\
def foo():
\t"""Hello foo."""
\tif True:
\t    x = 1
''',
            docformatter.format_code(
                unicode('''\
def foo():
\t"""
\tHello foo.
\t"""
\tif True:
\t    x = 1
''')))

    def test_format_code_with_escaped_newlines(self):
        self.assertEqual(
            r'''def foo():
    """Hello foo."""
    x = \
            1
''',
            docformatter.format_code(
                unicode(r'''def foo():
    """
    Hello foo.
    """
    x = \
            1
''')))

    def test_format_code_with_comments(self):
        self.assertEqual(
            r'''
def foo():
    """Hello foo."""
    # My comment
    # My comment with escape \
    123
'''.lstrip(),
            docformatter.format_code(
                unicode(r'''
def foo():
    """
    Hello foo.
    """
    # My comment
    # My comment with escape \
    123
'''.lstrip())))

    def test_format_code_skip_complex(self):
        """We do not handle r/u/b prefixed strings."""
        self.assertEqual(
            '''\
def foo():
    r"""
    Hello foo.
    """
''',
            docformatter.format_code(
                unicode('''\
def foo():
    r"""
    Hello foo.
    """
''')))

    def test_format_code_skip_complex_single(self):
        """We do not handle r/u/b prefixed strings."""
        self.assertEqual(
            """\
def foo():
    r'''
    Hello foo.
    '''
""",
            docformatter.format_code(
                unicode("""\
def foo():
    r'''
    Hello foo.
    '''
""")))

    def test_format_code_skip_nested(self):
        code = unicode("""\
def foo():
    '''Hello foo. \"\"\"abc\"\"\"
    '''
""")
        self.assertEqual(code, docformatter.format_code(code))

    def test_format_code_with_multiple_sentences(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo.

    This is a docstring.

    """
''',
            docformatter.format_code(
                unicode('''\
def foo():
    """
    Hello foo.
    This is a docstring.
    """
''')))

    def test_format_code_with_multiple_sentences_same_line(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo.

    This is a docstring.

    """
''',
            docformatter.format_code(
                unicode('''\
def foo():
    """
    Hello foo. This is a docstring.
    """
''')))

    def test_format_code_with_multiple_sentences_multiline_summary(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo.

    This is a docstring.

    """
''',
            docformatter.format_code(
                unicode('''\
def foo():
    """
    Hello
    foo. This is a docstring.
    """
''')))

    def test_format_code_with_empty_lines(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo.

    This is a docstring.

    More stuff.

    """
''',
            docformatter.format_code(
                unicode('''\
def foo():
    """
    Hello
    foo. This is a docstring.

    More stuff.
    """
''')))

    def test_format_code_with_trailing_whitespace(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo.

    This is a docstring.

    More stuff.

    """
''',
            docformatter.format_code(
                (unicode('''\
def foo():
    """
    Hello
    foo. This is a docstring.\t

    More stuff.\t
    """
'''))))

    def test_format_code_with_no_docstring(self):
        line = unicode('''\
def foo():
    "Just a regular string"
''')
        self.assertEqual(line, docformatter.format_code(line))

    def test_format_code_with_assignment_on_first_line(self):
        self.assertEqual(
            '''\
def foo():
    x = """Just a regular string. Alpha."""
''',
            docformatter.format_code(
                unicode('''\
def foo():
    x = """Just a regular string. Alpha."""
''')))

    def test_format_code_with_regular_strings_too(self):
        self.assertEqual(
            '''\
def foo():
    """Hello foo.

    This is a docstring.

    More stuff.

    """
    x = """My non-docstring
    This should not touched."""

    """More stuff
    that should not be
    touched\t"""
''',
            docformatter.format_code(
                unicode('''\
def foo():
    """
    Hello
    foo. This is a docstring.

    More stuff.
    """
    x = """My non-docstring
    This should not touched."""

    """More stuff
    that should not be
    touched\t"""
''')))

    def test_split_summary_and_description(self):
        self.assertEqual(('This is the first.',
                          'This is the second. This is the third.'),
                         docformatter.split_summary_and_description(
                         'This is the first. This is the second. This is the third.'))

    def test_split_summary_and_description_complex(self):
        self.assertEqual(('This is the first',
                          'This is the second. This is the third.'),
                         docformatter.split_summary_and_description(
                         'This is the first\n\nThis is the second. This is the third.'))

    def test_split_summary_and_description_more_complex(self):
        self.assertEqual(('This is the first.',
                          'This is the second. This is the third.'),
                         docformatter.split_summary_and_description(
                         'This is the first.\nThis is the second. This is the third.'))

    def test_split_summary_and_description_with_list(self):
        self.assertEqual(('This is the first',
                          '- one\n- two'),
                         docformatter.split_summary_and_description(
                         'This is the first\n- one\n- two'))

    def test_split_summary_and_description_with_list_on_other_line(self):
        self.assertEqual(('Test\n    test', '@blah'),
                         docformatter.split_summary_and_description('''\
    Test
    test
    @blah
'''))

    def test_split_summary_and_description_with_other_symbol(self):
        self.assertEqual(('This is the first',
                          '@ one\n@ two'),
                         docformatter.split_summary_and_description(
                         'This is the first\n@ one\n@ two'))

    def test_normalize_summary(self):
        self.assertEqual(
            'This is a sentence.',
            docformatter.normalize_summary('This \n\t is\na sentence'))

    def test_normalize_summary_with_different_punctuation(self):
        summary = 'This is a question?'
        self.assertEqual(
            summary,
            docformatter.normalize_summary(summary))

    def test_detect_encoding_with_bad_encoding(self):
        with temporary_file('# -*- coding: blah -*-\n') as filename:
            self.assertEqual('latin-1',
                             docformatter.detect_encoding(filename))


class TestSystem(unittest.TestCase):

    def test_diff(self):
        with temporary_file('''\
def foo():
    """
    Hello world
    """
''') as filename:
            output_file = io.StringIO()
            docformatter.main(argv=['my_fake_program', filename],
                              standard_out=output_file,
                              standard_error=None)
            self.assertEqual(unicode('''\
@@ -1,4 +1,2 @@
 def foo():
-    """
-    Hello world
-    """
+    """Hello world."""
'''), '\n'.join(output_file.getvalue().split('\n')[2:]))

    def test_diff_with_nonexistent_file(self):
        output_file = io.StringIO()
        docformatter.main(argv=['my_fake_program', 'nonexistent_file'],
                          standard_out=output_file,
                          standard_error=output_file)
        self.assertIn('no such file', output_file.getvalue().lower())

    def test_in_place(self):
        with temporary_file('''\
def foo():
    """
    Hello world
    """
''') as filename:
            output_file = io.StringIO()
            docformatter.main(argv=['my_fake_program', '--in-place', filename],
                              standard_out=output_file,
                              standard_error=None)
            with open(filename) as f:
                self.assertEqual('''\
def foo():
    """Hello world."""
''', f.read())

    def test_ignore_hidden_directories(self):
        with temporary_directory() as directory:
            with temporary_directory(prefix='.',
                                     directory=directory) as inner_directory:

                with temporary_file('''\
def foo():
    """
    Hello world
    """
''', directory=inner_directory):

                    output_file = io.StringIO()
                    docformatter.main(argv=['my_fake_program',
                                            '--recursive',
                                            directory],
                                   standard_out=output_file,
                                   standard_error=None)
                    self.assertEqual(
                        '',
                        output_file.getvalue().strip())

    def test_end_to_end(self):
        with temporary_file('''\
def foo():
    """
    Hello world
    """
''') as filename:
            import subprocess
            process = subprocess.Popen(['./docformatter', filename],
                                       stdout=subprocess.PIPE)
            self.assertEqual('''\
@@ -1,4 +1,2 @@
 def foo():
-    """
-    Hello world
-    """
+    """Hello world."""
''', '\n'.join(process.communicate()[0].decode('utf-8').split('\n')[2:]))

    def test_end_to_end_with_wrapping(self):
        with temporary_file('''\
def foo():
    """
    Hello world this is a summary that will get wrapped
    """
''') as filename:
            import subprocess
            process = subprocess.Popen(['./docformatter',
                                        '--wrap-summaries=40',
                                        filename],
                                       stdout=subprocess.PIPE)
            self.assertEqual('''\
@@ -1,4 +1,3 @@
 def foo():
-    """
-    Hello world this is a summary that will get wrapped
-    """
+    """Hello world this is a summary
+    that will get wrapped."""
''', '\n'.join(process.communicate()[0].decode('utf-8').split('\n')[2:]))

    def test_end_to_end_all_options(self):
        self.maxDiff = None

        with temporary_file('''\
def foo():
    """Hello world is a long sentence that will be wrapped at 40 characters because I'm using that option
    - My list item
    - My list item


    """
''') as filename:
            import subprocess
            process = subprocess.Popen(['./docformatter',
                                        '--wrap-summaries=40',
                                        '--pre-summary-newline',
                                        '--no-blank',
                                        filename],
                                       stdout=subprocess.PIPE)
            self.assertEqual('''\
@@ -1,7 +1,9 @@
 def foo():
-    """Hello world is a long sentence that will be wrapped at 40 characters because I'm using that option
+    """
+    Hello world is a long sentence that
+    will be wrapped at 40 characters
+    because I'm using that option.
+
     - My list item
     - My list item
-
-
     """
''', '\n'.join(process.communicate()[0].decode('utf-8').split('\n')[2:]))

    def test_no_arguments(self):
        import subprocess
        process = subprocess.Popen(['./docformatter'],
                                   stderr=subprocess.PIPE)
        self.assertIn('arguments',
                      process.communicate()[1].decode('utf-8'))


def generate_random_docstring(max_indentation_length=32,
                              max_word_length=20,
                              max_words=50):
    """Generate single-line docstring."""
    import random
    if random.randint(0, 1):
        words = []
    else:
        words = [generate_random_word(random.randint(0, max_word_length))
                 for _ in range(random.randint(0, max_words))]

    indentation = random.randint(0, max_indentation_length) * ' '
    quote = '"""' if random.randint(0, 1) else "'''"
    return (quote + indentation +
            ' '.join(words) +
            quote)


def generate_random_word(word_length):
    import random
    return ''.join(
        [random.choice('abcdefghijklmnoprstuvwyxzABCDEFGHIJKLMNOPRSTUVWXYZ')
         for _ in range(word_length)])


@contextlib.contextmanager
def temporary_file(contents, directory='.', prefix=''):
    """Write contents to temporary file and yield it."""
    f = tempfile.NamedTemporaryFile(suffix='.py', prefix=prefix,
                                    delete=False, dir=directory)
    try:
        f.write(contents.encode('utf8'))
        f.close()
        yield f.name
    finally:
        import os
        os.remove(f.name)


@contextlib.contextmanager
def temporary_directory(directory='.', prefix=''):
    """Create temporary directory and yield its path."""
    temp_directory = tempfile.mkdtemp(prefix=prefix, dir=directory)
    try:
        yield temp_directory
    finally:
        import shutil
        shutil.rmtree(temp_directory)


if __name__ == '__main__':
    unittest.main()

import textwrap
import unittest

from zzyzx import markdownify


def d(text):
    """Test-specific dedent.

    Drops the initial newline.

    The # character is replaced with nothing, which lets us format strings
    with effective trailing whitespace.
    """
    result = textwrap.dedent(text)
    if result.startswith('\n'):
        result = result[1:]
    result = result.replace('#', '')
    return result


class MarkdownifyTest(unittest.TestCase):
    def test_apple_notes_whitespace(self):
        html = d("""
            <div>One</div><div><br></div>Two<div>Three</div><div><br></div>
            <div>Four</div>
        """)
        expected = d("""
        One

        TwoThree

        Four
        """)
        actual = markdownify.markdownify(html)
        self.assertEqual(expected, actual)

    def test_strange_lists(self):
        html = d("""
            <ol>
            <li>Yeah</li>
            <li>Yeah</li>
            <li>Yeah</li>
            <ol>
            <li>Nope</li>
            <li>Nope</li>
            <li>Nope
            <ol>
            <li>Maybe</li>
            <li>Maybe</li>
            <li>Maybe</li>
            </ol>
            </li>
            </ol>
            <li>Yeah</li>
            <li>Yeah</li>
            <li>Yeah</li>
            </ol>
        """)
        expected = d("""
            1. Yeah
            2. Yeah
            3. Yeah

            \t1. Nope
            \t2. Nope
            \t3. Nope #
            \t\t1. Maybe
            \t\t2. Maybe
            \t\t3. Maybe
            \t\t#
            \t#
            \t#
            4. Yeah
            5. Yeah
            6. Yeah
        """)
        actual = markdownify.markdownify(html)
        self.assertEqual(expected, actual, '\n' + repr(expected) + '\n' + repr(actual))


if __name__ == '__main__':
    unittest.main()

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
    result = result.replace('?', '')
    return result


class MarkdownifyTest(unittest.TestCase):
    def test_apple_notes_whitespace(self):
        html = d("""
            <div>One</div><div><br></div>Two<div>Three</div><div><br></div>
            <div>Four</div>
        """)
        expected = d("""
        # One


        TwoThree

        Four
        """)
        actual = markdownify.MarkdownConverter().convert(html)
        self.assertEqual(expected, actual)

    def test_apple_notes_whitespace2(self):
        html = d("""
            One<div><br></div>Two<div>Three</div><div><br></div>
            <div>Four</div>
        """)
        expected = d("""
        # One


        TwoThree

        Four
        """)
        actual = markdownify.MarkdownConverter().convert(html)
        self.assertEqual(expected, actual)

    def test_apple_notes_whitespace3(self):
        html = d("""
            One<div>Two</div><div>Three</div><div><br></div>
            <div>Four</div>
        """)
        expected = d("""
        # One

        Two
        Three

        Four
        """)
        actual = markdownify.MarkdownConverter().convert(html)
        self.assertEqual(expected, actual)

    def test_apple_notes_whitespace3(self):
        html = d("""
            <div>One</div><div>Two</div><div>Three</div><div><br></div>
            <div>Four</div>
        """)
        expected = d("""
        # One

        Two
        Three

        Four
        """)
        actual = markdownify.MarkdownConverter().convert(html)
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
            <ul>
            <li>Yeah</li>
            <li>Yeah</li>
            <li>Yeah</li>
            <ul>
            <li>Nope</li>
            <li>Nope</li>
            <li>Nope
            <ul>
            <li>Maybe</li>
            <li>Maybe</li>
            <li>Maybe</li>
            </ul>
            </li>
            </ul>
            <li>Yeah</li>
            <li>Yeah</li>
            <li>Yeah</li>
            </ul>
        """)
        expected = d("""
            1. Yeah
            2. Yeah
            3. Yeah
            \t1. Nope
            \t2. Nope
            \t3. Nope \t?
            \t\t1. Maybe
            \t\t2. Maybe
            \t\t3. Maybe
            4. Yeah
            5. Yeah
            6. Yeah

            * Yeah
            * Yeah
            * Yeah
            \t+ Nope
            \t+ Nope
            \t+ Nope \t?
            \t\t- Maybe
            \t\t- Maybe
            \t\t- Maybe
            * Yeah
            * Yeah
            * Yeah
        """)
        actual = markdownify.MarkdownConverter().convert(html)
        self.assertEqual(
            expected,
            actual,
            '\n' + repr(expected) + '\n' + repr(actual)
        )


if __name__ == '__main__':
    unittest.main()

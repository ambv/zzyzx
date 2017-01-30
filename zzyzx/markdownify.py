#!/usr/bin/env python3

from functools import partial
import re

from bs4 import BeautifulSoup, NavigableString

line_beginning_re = re.compile(r'^', re.MULTILINE)
whitespace_re = re.compile(r'[\r\n\t ]+', re.MULTILINE)
triple_line_re = re.compile(r'\n\n\n', re.MULTILINE)
FRAGMENT_ID = '__MARKDOWNIFY_WRAPPER__'
wrapped = '<div id="%s">%%s</div>' % FRAGMENT_ID


# Heading styles
ATX = 'atx'
ATX_CLOSED = 'atx_closed'
UNDERLINED = 'underlined'
SETEXT = UNDERLINED


def escape(text):
    if not text:
        return ''
    return text.replace('_', r'\_')


def _todict(obj):
    return dict((k, getattr(obj, k)) for k in dir(obj) if not k.startswith('_'))


class MarkdownConverter:
    class Options:
        heading_style = ATX
        bullets = '*+-'  # An iterable of bullet types.

    def __init__(self, **options):
        self.options = _todict(self.Options)
        self.options.update(options)
        self.convert_h1 = partial(self.convert_hn, n=1)
        self.convert_h2 = partial(self.convert_hn, n=2)
        self.convert_h3 = partial(self.convert_hn, n=3)
        self.convert_h4 = partial(self.convert_hn, n=4)
        self.convert_h5 = partial(self.convert_hn, n=5)
        self.convert_h6 = partial(self.convert_hn, n=6)
        self.convert_h7 = partial(self.convert_hn, n=7)
        self.convert_h8 = partial(self.convert_hn, n=8)
        self.convert_h9 = partial(self.convert_hn, n=9)

    def convert(self, html):
        if "<html>" in html or "<body>" in html:
            soup = BeautifulSoup(html, "html5lib")
            tag = soup.find("body")
        else:
            soup = BeautifulSoup(wrapped % html, "html5lib")
            tag = soup.find(id=FRAGMENT_ID)

        return self.process_tag(tag, is_main_document=True)

    def process_tag(self, node, is_main_document=False):
        text = ''
        tags_found = False

        # Convert the children first
        for el in node.children:
            if isinstance(el, NavigableString):
                text += self.process_text(str(el))
            else:
                if is_main_document and not tags_found:
                    # Apple Notes' title is just text crammed into the body
                    # without any tags.
                    if text:
                        text += '\n'
                        if len(text) < 80:
                            # Naive heuristic but better than nothing.
                            text = '# ' + text
                    tags_found = True
                text += self.process_tag(el)

        if not is_main_document:
            convert_fn = getattr(self, 'convert_%s' % node.name, None)
            if convert_fn:
                text = convert_fn(node, text)

        return text

    def process_text(self, text):
        if text == '\n':
            return ''
        return escape(whitespace_re.sub(' ', text or ''))

    def indent(self, text, level):
        return line_beginning_re.sub('\t' * level, text) if text else ''

    def underline(self, text, pad_char):
        text = (text or '').rstrip()
        return '%s\n%s\n\n' % (text, pad_char * len(text)) if text else ''

    def convert_a(self, el, text):
        href = el.get('href')
        title = el.get('title')
        if text == href and not title:
            # Shortcut syntax
            return '<%s>' % href
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        return '[%s](%s%s)' % (text or '', href, title_part) if href else text or ''

    def convert_blockquote(self, el, text):
        return '\n' + line_beginning_re.sub('> ', text) if text else ''

    def convert_br(self, el, text):
        return '\n'

    def convert_em(self, el, text):
        return '*%s*' % text if text else ''

    def convert_hn(self, el, text, n=1):
        style = self.options['heading_style']
        text = text.rstrip()
        if style == UNDERLINED and n <= 2:
            line = '=' if n == 1 else '-'
            return self.underline(text, line)
        hashes = '#' * n
        if style == ATX_CLOSED:
            return '%s %s %s\n\n' % (hashes, text, hashes)
        return '%s %s\n\n' % (hashes, text)

    def convert_i(self, el, text):
        return self.convert_em(el, text)

    def convert_list(self, el, text):
        level = -1
        while el:
            if el.name in ('li', 'ol', 'ul'):
                level += 1
            el = el.parent
        if level:
            text = '\n' + self.indent(text, 1) + '\n'
        return text

    convert_ul = convert_list
    convert_ol = convert_list

    def convert_li(self, el, text):
        parent = el.parent
        if parent is not None and parent.name == 'ol':
            index = 0
            for ch in parent.children:
                if ch.name == 'li':
                    index += 1
                if ch is el:
                    break
            bullet = '%s.' % (index)
        else:
            depth = -1
            while el:
                if el.name == 'ul':
                    depth += 1
                el = el.parent
            bullets = self.options['bullets']
            bullet = bullets[depth % len(bullets)]
        return '%s %s\n' % (bullet, text or '')

    def convert_div(self, el, text):
        text = text.rstrip()
        return '%s\n' % text

    def convert_p(self, el, text):
        text = text.rstrip()
        return '%s\n\n' % text

    def convert_strong(self, el, text):
        return '**%s**' % text if text else ''

    convert_b = convert_strong

    def convert_img(self, el, text):
        alt = el.attrs.get('alt', None) or ''
        src = el.attrs.get('src', None) or ''
        title = el.attrs.get('title', None) or ''
        title_part = ' "%s"' % title.replace('"', r'\"') if title else ''
        return '![%s](%s%s)' % (alt, src, title_part)

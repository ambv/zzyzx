#!/usr/bin/env python3

import email.policy
import email.parser
import email.utils
import mimetypes
import os

import click

from zzyzx import util

try:
    import magic
    from zzyzx import markdownify
except ImportError:
    markdownify = None


@util.pass_cfg
def md(cfg):
    """Reverse-engineers HTML notes to Markdown."""

    if 'markdown' not in cfg or 'path' not in cfg['markdown']:
        raise RuntimeError("Add a [markdown] section to your configuration.")

    ext = cfg['markdown'].get('extension', '.txt')
    converter = markdownify.MarkdownConverter(
        heading_style=cfg['markdown'].get('headings', 'atx'),
    )
    use_tags = cfg['markdown'].getboolean('use_tags')
    tag = None

    repo_path = os.path.realpath(os.path.expanduser(cfg['backup']['repo_path']))
    try:
        markdown_path = os.path.realpath(
            os.path.expanduser(cfg['markdown']['path'])
        )
    except KeyError:
        raise click.ClickException(
            '`path` not found under [markdown] section in configuration',
        ) from None

    existing_files = set(util.gen_existing_files(markdown_path))
    eml_files = set(
        map(
            lambda fn: fn[len(repo_path) + 1:],
            filter(
                lambda fn: fn.endswith('.eml'),
                util.gen_existing_files(repo_path),
            ),
        ),
    )
    for eml in eml_files:
        txt = eml[:-4] + ext
        eml_path = os.path.join(repo_path, eml)
        txt_path = os.path.join(markdown_path, txt)
        if use_tags:
            tag = os.path.dirname(txt).replace(' ', '-')
        saved_files = extract_files(eml_path, txt_path, converter, tag=tag)
        existing_files -= saved_files
    for f in sorted(existing_files):
        click.echo('Deleting stale file {}'.format(f))
        os.unlink(f)


def extract_files(
    src,
    dst,
    converter,
    tag=None,
    email_parser=email.parser.BytesParser(policy=email.policy.default),
):
    click.echo('{} -> {}'.format(src, dst))
    files = set()
    basename, _ = os.path.splitext(dst)
    with open(src, 'rb') as eml:
        msg = email_parser.parse(eml)
    created = email.utils.parsedate_to_datetime(
        msg['x-mail-created-date'],
    )
    modified = email.utils.parsedate_to_datetime(
        msg['date'],
    )
    text_parts = {}
    counter = 0
    for part in msg.walk():
        if part.get_content_maintype() == 'multipart':
            continue  # just metadata, give me the meat

        data = part.get_payload(decode=True)
        if part.get_content_maintype() == 'text':
            subtype = part.get_content_subtype()
            text_parts[subtype] = data.decode(part.get_content_charset())
        else:
            counter += 1
            content_type = magic.from_buffer(data, mime=True)
            ext = guess_extension(content_type)
            filename = ''.join((basename, str(counter), ext))
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'wb') as f:
                f.write(data)
                files.add(filename)
    html = text_parts.pop('html', None)
    txt = text_parts.pop('plain', None)
    if html:
        html = converter.convert(html)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w') as f:
            f.write(html)
            if tag:
                f.write('\n#{}\n'.format(tag))
            files.add(dst)
    elif txt:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, 'w') as f:
            f.write(txt)
            if tag:
                f.write('\n#{}\n'.format(tag))
            files.add(dst)
    for filetype, data in text_parts.items():
        click.secho(
            'warning: unknown text subtype for `{}`: {}'
            ''.format(src, filetype),
            fg='yellow',
        )
        filename = '.'.join((dst, filetype))
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w') as f:
            f.write(data)
            if tag:
                f.write('\n#{}\n'.format(tag))
            files.add(filename)
    for f in files:
        # note: we're cheating, putting creation time as access time
        os.utime(f, (created.timestamp(), modified.timestamp()))
    return files


def guess_extension(content_type):
    """Like mimetypes.guess_extension but deterministic across executions."""

    if isinstance(content_type, bytes):
        content_type = content_type.decode('ascii')
    exts = mimetypes.guess_all_extensions(content_type)
    if exts:
        ext = list(sorted(sorted(exts), key=lambda e: len(e)))[-1]
    else:
        ext = None
    if not ext:
        ext = '.bin'
    return ext


if markdownify:
    md = util.cli.command()(md)

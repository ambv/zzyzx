#!/usr/bin/env python3

from collections import namedtuple
import configparser
from contextlib import contextmanager
from functools import cmp_to_key
from functools import update_wrapper
import getpass
import imaplib
import locale
import os
import re
import shutil
import subprocess
from tempfile import NamedTemporaryFile
import unicodedata

import click
import pkg_resources

try:
    locale.setlocale(locale.LC_ALL, "")
except locale.Error:
    pass


class ExpandUserPath(click.Path):
    def convert(self, value, param, ctx):
        return super().convert(os.path.expanduser(value), param, ctx)


@click.group()
@click.option(
    '--config-path',
    default='~/.zzyzx',
    type=ExpandUserPath(exists=True, dir_okay=False, allow_dash=True),
    help='Where to find the INI file with configuration.',
)
@click.pass_context
def cli(ctx, config_path):
    """The last Notes manager on Earth."""
    cfg = configparser.RawConfigParser()
    cfg.read([config_path])
    ctx.obj['cfg'] = cfg


def pass_cfg(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        cfg = ctx.obj['cfg']
        return ctx.invoke(f, cfg, *args, **kwargs)
    return update_wrapper(new_func, f)


def get_user():
    click.echo('Username: ', nl=False)
    return input().strip()


@contextmanager
def imap_connection(cfg):
    srv = cfg['server']
    conn = imaplib.IMAP4_SSL(srv['host'])
    try:
        if not srv.get('user'):
            srv['user'] = get_user()
        if not srv.get('pass'):
            srv['pass'] = getpass.getpass()
        try:
            conn.login(srv['user'], srv['pass'])
        finally:
            # don't snoop my password, man.
            del srv['user']
            del srv['pass']
        yield conn
    finally:
        try:
            conn.close()
        except conn.error:
            pass
        conn.logout()


list_response_pattern = re.compile(
    br'''
        \((?P<flags>.*?)\)
        [ ]
        "(?P<delimiter>.*)"
        [ ]
        (?P<name_querysafe>
            (?P<_namequote>")?
            (?P<name>.*)
            (?(_namequote)")
        )
    ''',
    re.X,
)


list_response = namedtuple(
    'list_response',
    'name delimiter flags name_querysafe',
)


def parse_list_response(line):
    m = list_response_pattern.match(line)
    if not m:
        return None

    return list_response(
        m.group('name').replace(b'&', b'+').decode('utf7'),
        m.group('delimiter').decode('ascii'),
        m.group('flags').decode('ascii').split(),
        m.group('name_querysafe'),
    )


@cmp_to_key
def _list_response_key(d1, d2):
    # FIXME: collation rules for Polish are broken on most systems
    # so this doesn't really help. PyICU would be needed.
    return locale.strcoll(d1.name, d2.name)


def parse_list_responses(lines):
    result = []
    for line in lines:
        d = parse_list_response(line or b'')
        if d is None:
            continue

        result.append(d)
    result.sort(key=_list_response_key)
    return result


def gen_existing_files(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            yield unicodedata.normalize('NFD', os.path.join(root, file))


def gen_existing_dirs(path):
    for dirpath, dirnames, filenames in os.walk(path):
        for dirname in {'.hg', '.git'}:
            # don't recurse into version-control directories
            if dirname in dirnames:
                dirnames.remove(dirname)

        for dirname in dirnames:
            yield unicodedata.normalize('NFD', os.path.join(dirpath, dirname))


def delete_directories(dirs_to_delete):

    def report_failures(func, path, excinfo):
        click.secho(
            'warning: cannot delete {}, reason: {}'.format(path, excinfo[1]),
            fg='yellow',
        )

    for d in reversed(sorted(dirs_to_delete)):
        click.echo('Unlinking stale directory {}'.format(d))
        shutil.rmtree(d, onerror=report_failures)


def delete_files(notes_dir, files_to_delete):
    for f in files_to_delete:
        click.echo('Unlinking stale file {}'.format(f))
        try:
            os.unlink(os.path.join(notes_dir, f))
        except OSError as e:
            click.secho(
                'warning: cannot delete {}, reason: {}'.format(f, e),
                fg='yellow',
            )


def make_filename_safe(name):
    name = name[:64]

    for ch in '?:"\r\n,;':
        name = name.replace(ch, '')

    name = name.strip()

    if name.endswith('.'):
        name = name[:-1]

    name = name.lower()

    name = name.replace('/', '_')
    name = name.replace('\\', '_')
    name = name.replace(' ', '_')
    name = name.replace('\t', '_')
    name = name.replace('\n', '_')
    while '__' in name:
        name = name.replace('__', '_')
    name = unicodedata.normalize('NFD', name)

    return name


def has_hg(hg):
    try:
        subprocess.run(
            [hg, '--version'],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        return True

    except (OSError, subprocess.CalledProcessError):
        click.echo(
            'warning: hg unavailable, history will not be stored',
            fg='yellow',
        )
        return False


def hg_init(hg, repo_path):
    if os.path.exists(os.path.join(repo_path, '.hg')):
        return

    old_cwd = os.getcwd()
    try:
        os.chdir(repo_path)
        subprocess.run(
            [hg, 'init'],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    except (OSError, subprocess.CalledProcessError):
        click.secho(
            'warning: hg init failed, history will not be stored',
            fg='yellow',
        )
    finally:
        os.chdir(old_cwd)


def hg_commit(hg, repo_path, metadata):
    old_cwd = os.getcwd()
    try:
        os.chdir(repo_path)
        proc = subprocess.run(
            [hg, 'status'],
            check=True,
            stdout=subprocess.PIPE,
        )
    except (OSError, subprocess.CalledProcessError):
        click.secho(
            'warning: hg status failed, history will not be stored',
            fg='yellow',
        )
        return

    finally:
        os.chdir(old_cwd)

    if not proc.stdout:
        click.echo('Nothing to commit.')
        return

    with NamedTemporaryFile('w+', prefix='commit', suffix='.txt') as commit_msg:
        template = pkg_resources.resource_string('zzyzx', 'commit_message.txt')
        template = template.decode('utf8').format(**metadata)
        commit_msg.write(template)
        commit_msg.flush()
        click.echo('Committing changes...')
        click.echo(template)

        old_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            proc = subprocess.run(
                [hg, 'commit', '-A', '-u', 'zzyzx', '-l', commit_msg.name],
                check=True,
            )
        except (OSError, subprocess.CalledProcessError):
            click.secho(
                'warning: hg commit failed, history will not be stored',
                fg='yellow',
            )
            return

        finally:
            os.chdir(old_cwd)

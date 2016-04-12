#!/usr/bin/env python3

import email.policy
import email.parser
import email.utils
import os
import time
import unicodedata

import click

from zzyzx import util


@util.cli.command()
@util.pass_cfg
def backup(cfg):
    """Backs up remote IMAP notes in a local Mercurial repository."""

    repo_path = os.path.realpath(os.path.expanduser(cfg['backup']['repo_path']))
    hg_path = os.path.expanduser(cfg['backup'].get('hg_path', 'hg'))
    if hg_path and util.has_hg(hg_path):
        util.hg_init(hg_path, repo_path)
    else:
        hg_path = None
    ignore_prefix = cfg['backup'].get('ignore_prefix')
    metadata = {
        'start_time': time.time(),
        'updated_files': 0,
        'updated_dirs': 0,
        'deleted_files': 0,
        'deleted_dirs': 0,
    }
    with util.imap_connection(cfg) as conn:
        result, mailboxes = conn.list('INBOX.Notes')
        if result != 'OK':
            raise click.ClickException(
                'searching for INBOX.Notes failed with {}'.format(result),
            )

        old_dirs = set(util.gen_existing_dirs(repo_path))
        updated_dirs = set()
        for d in util.parse_list_responses(mailboxes):
            click.secho(d.name, fg='red', bold=True)
            notes_dir = create_directories(d.name, repo_path, ignore_prefix)

            def symlink_or_file(path):
                """Like os.path.isfile(path) but returns True for broken symlinks."""
                p = os.path.join(notes_dir, path)
                return os.path.islink(p) or os.path.isfile(p)

            old_files = set(
                map(
                    lambda fn: unicodedata.normalize('NFD', fn),
                    filter(symlink_or_file, os.listdir(notes_dir)),
                ),
            )
            updated_files = backup_mailbox(conn, d, notes_dir)
            util.delete_files(notes_dir, old_files - updated_files)
            updated_dirs.add(notes_dir)
            metadata['updated_dirs'] += 1
            metadata['updated_files'] += len(updated_files)
            metadata['deleted_files'] += len(old_files - updated_files)

    util.delete_directories(old_dirs - updated_dirs)
    metadata['deleted_dirs'] = len(old_dirs - updated_dirs)
    metadata['duration'] = time.time() - metadata['start_time']
    if hg_path:
        util.hg_commit(hg_path, repo_path, metadata)



def backup_mailbox(
    conn,
    d,
    notes_dir,
    email_parser=email.parser.BytesParser(policy=email.policy.default),
):
    updated_files = {}

    conn.select(d.name_querysafe, readonly=True)
    typ, data = conn.search(None, 'ALL')
    for num in data[0].split():
        typ, data = conn.fetch(num, '(RFC822)')
        msg = email_parser.parsebytes(data[0][1])
        imap_id = msg['Message-Id']
        note_uuid = msg['X-Universally-Unique-Identifier']
        created = email.utils.parsedate_to_datetime(
            msg['x-mail-created-date'],
        )
        modified = email.utils.parsedate_to_datetime(
            msg['date'],
        )
        body = msg.get_body()

        filename = '.' + note_uuid
        backup_path = os.path.join(notes_dir, filename)
        with open(backup_path, 'wb') as backup_file:
            backup_file.write(data[0][1])
        # note: we're cheating, putting creation time as access time
        os.utime(backup_path, (created.timestamp(), modified.timestamp()))
        updated_files[filename] = msg['subject']

        click.secho('{}) '.format(num.decode('ascii')), fg='green', nl=False)
        click.echo(created, nl=False)
        click.secho(' {}'.format(msg['subject']), bold=True)

    symlink_uuids_to_human_readable_titles(updated_files, notes_dir)
    return set(updated_files)


def create_directories(d_name, repo_path, ignore_prefix=None):
    if ignore_prefix and d_name.startswith(ignore_prefix):
        d_name = d_name[len(ignore_prefix):]
        while d_name.startswith('.'):
            d_name = d_name[1:]
    path = os.path.join(repo_path, d_name.replace('.', os.sep))
    os.makedirs(
        path,
        mode=0o700,
        exist_ok=True,
    )
    return path


def symlink_uuids_to_human_readable_titles(updated_files, notes_dir):
    paths = {}
    for uuid, title in updated_files.items():
        title = util.make_filename_safe(title)
        i = 0
        while title in paths.values():
            title += uuid[i]
            i += 1
        paths[uuid] = title + '.eml'

    for uuid, title in paths.items():
        src = os.path.join(notes_dir, uuid)
        dst = os.path.join(notes_dir, title)
        if os.path.exists(dst):
            os.unlink(dst)
        os.symlink(src, dst)
        updated_files[title] = None


def main():
    backup()


if __name__ == '__main__':
    main()


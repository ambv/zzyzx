=====
zzyzx
=====

Do you believe in the cloud? It's in fact only somebody else's computer.
Those might fail or get hacked.

Do you believe in bug-free software? Nah, it's more likely every now and
then a crash, a bug, a race condition or some other back luck will lead
to data corruption of the things that you work on.

Do you think you'll be able to access your notes in thirty years? It's
likely the data format they're stored in is going to be hard to read.

This is why I store all my notes in my e-mail. It's been there since the
1970s, it's going to be there in the 2050s. MIME and IMAP ensure the
data is more-less plaintext and easily human-readable even without any
tool support. Apple Notes support it on both OS X and iOS. Pure win.

But wait, what about software failure? What if a bug erases my notes or
there's a data center fire and the data restored from a backup is in
a state from two days ago? What about bitrot?

Enter ``zzyzx``.

This is the most primitive backup system ever. Set it up in cron on your
laptop or a server you control and it will create incremental backups
with history between runs (setting up a Mercurial repository). It also
creates useful symlinks to human-readable note titles so you can find
them more easily.


Installation
------------

It requires Python 3.5+ and Click. Just install it from PyPI::

   $ pip install zzyzx
   $ cat >~/.zzyzx
   [server]
   host=mail.example.com
   user=john@example.com
   pass=secret

   [backup]
   repo_path=~/Notes
   ignore_prefix=INBOX.Notes

   [markdown]
   path=~/Dropbox/Notes
   $ zzyzx backup
   $ zzyzx md


Why the name ``zzyzx``?
-----------------------

It's the last place on Earth. It's the end of the world.


Known issues
------------

Don't put the repo path in Dropbox as it doesn't support symlinks and
your other computers will see a lot of duplicate files.


Changes
-------

2016.6.0
~~~~~~~~

* bugfix: slashes and backslashes weren't properly escaped for title
  symlinks

2016.4.1
~~~~~~~~

* backwards incompatible: ``zzyzx`` functionality now available as
  ``zzyzx backup``
* new functionality: ``zzyzx md`` unpacks .eml into text files and
  attachments, translating HTML into Markdown
* bugfix: existing and newly created filenames are normalized to NFD;
  existing file tracking won't be so eager to delete files anymore on
  OS X

2016.4.0
~~~~~~~~

* first published version


Authors
-------

Glued together by `Łukasz Langa <lukasz@langa.pl>`.

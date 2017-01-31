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
   $ zzyzx backup


Markdown export
---------------

If you installed ``zzyzx[markdown]`` from PyPI, you can also run::

   $ zzyzx md

This will generate a list of files that are a textual representation
of the notes' contents. This is useful for exporting Apple Notes into
systems that expect Markdown files, like
`Bear <http://www.bear-writer.com/>`_.

Configure your Markdown support adding a section like the following
to your `.zzyzx` config::

   [markdown]
   path=~/Dropbox/Notes
   extension=.txt
   headings=atx

Headings can be "atx" (simple hashes), "atx_closed" (symmetrical
hashes), or "underlined" (ReST-like).


Why the name ``zzyzx``?
-----------------------

It's the last place on Earth. It's the end of the world.


Known issues
------------

Don't put the repo path in Dropbox as it doesn't support symlinks and
your other computers will see a lot of duplicate files.

The Markdown export is not perfect because the HTML syntax used by
Apple Notes is pretty strange. I did what I could, tested against a few
hundred notes against macOS Sierra and iOS 10.2 (they are not consistent
between each other either).


Changes
-------

???
~~~

* feature: ignore version control directories when backing up or
  exporting to Markdown
* feature: keep modification dates in journal-style notes consistent
* bugfix: for `.md` exports, disambiguate titles from content
* bugfix: for `.md` exports, don't produce vertical whitespace for nested
  lists

2017.1.0
~~~~~~~~

* the Markdown export update: generally sucks less
* also update the creation and modification date in the Markdown export
* allow customization of the Markdown export file extensions
* allow exporting folder-based hashtags (for example for use with Bear
  editor)

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

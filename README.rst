What is shup?
=============

shup is a small tool made for those who care about sharing files, or
simply for those who want to frequently upload files to some redundant
targets. The primary reason why shup was built is uploading files to a
directory under the supervision of an http server so that it becomes
super easy to share files with urls like
http://files.example.com/surprise.png just by running:

``shup mywebsite ~/Pictures/surprise.png``

*mywebsite* is a rule, we’ll see that later.

.. figure:: https://files.naam.me/shup/screencast.gif
   :alt: Demo

   Demo

Install
=======

To install the few needed dependencies run a variant of:
``python pip install --user -r requirements.txt`` on your local machine.
Also be sure to have ``at`` command on your remote machines (and the atd
running):

-  `Debian <https://packages.qa.debian.org/a/at.html>`__
-  `Arch <https://www.archlinux.org/packages/community/i686/at/>`__
-  `CentOs 7 <http://mirror.centos.org/centos/7/os/x86_64/Packages/>`__

For now there is no official installer so drop shup in your *~/bin* or
any other folder in your *$PATH* you like.

How to use it?
==============

Intro
-----

Let’s say you own example.com and the subdomain files.example.com point
to a directory managed by your http server like */www/static/*. The goal
of shup is to avoid doing the same boring thing everytime. Let’s write a
basic configuration rule once for this directory on example.com. If you
have the same session name on your remote machine as your local machine,
no need to specify it. Let’s say you also want that every file expire
one week after creation by default on that directory. Since we dont
share critical info here no need to use anything else than simple ``rm``
command for deletion. Here is the configuration you would write for this
situation:

::

    [example_static]
    ssh_host = example.com
    file_path = /www/static
    file_ttl = 1w

Now we can start uploading file as simply as:
``shup -u example_static look_at_this.webm``. As the arguments supersede
the configuration files we can also overwrite the TTL of the file and
the way it’s deleted for example:
``shup -t 2h -d 'shred -n 200 -z -u' -u example_static sensible_file.tar.bz2``

Configuration files
-------------------

shup will automatically try to read configurations files (*shup.cfg*) in
both ``/etc/shup/shup.cfg`` and ``~/.config/shup/shup.cfg`` in that
order. Please note that the latter supersede the former as the arguments
do with configuration files. A default target should be specified in one
of the configuration files in order to use shup withou the rule argument
(``-u``).

Help
----

Here is the output of ``shup -h``:

::

    usage: shup [-h] [-u name] [-v] [-d path] [-t time] [-p perms] [-l ret]
                [-r | -c | --cksum algorithm]
                file [file ...]

    positional arguments:
      file                  file that should be upload following the rule given by
                            the optional `--rule' argument

    optional arguments:
      -h, --help            show this help message and exit
      -u name, --rule name  target rule to follow, contains everything from host
                            informations to the destination folder and the TTL of
                            the file if specified. If not specified, shup search
                            for a section 'default' in the configuration files
      -v, --verbose         increase the output verbosity during the operation
                            (increase with vv or vvv)
      -d path, --delwith path
                            set the binary used to delete the binary when the TTL
                            reach 0
      -t time, --ttl time   set the time while the file will stay on the remote
                            host before being deleted
      -p perms, --permissions perms
                            set the file permissions in octal mode, default is
                            0644
      -l ret, --file-return ret
                            set the file return path
      -r, --randomize       randomize filename
      -c                    replace the filename by the file's checksum following
                            'file_cksum' rule in configuration files or SHA1 if
                            nothing specified
      --cksum algorithm     like -c but following the command line argument
                            'algorithm'

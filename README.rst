=========
SublimeHg
=========

Issue commands to Mercurial from Sublime Text.


Requirements
============

* Mercurial 1.9 or above (command server)


Getting Started
===============

- `Download`_ and install SublimeHg. (See `installation instructions`_ for ``.sublime-package`` files.)

.. _Download: https://bitbucket.org/guillermooo/downloads/sublimehg.sublime-package
.. _installation instructions: http://sublimetext.info/docs/en/extensibility/packages.html#installation-of-packages


Configuration
=============

By default, SublimeHg uses ``hg`` as the default executable name for Mercurial.
If you need to use a different one, like ``hg.bat``, set the variable
``packages.sublime_hg.hg_exe`` to it in your global settings (**Preferences | User Global Settings**).

Example::

   {
      "packages.sublime_hg.hg_exe": "hg.bat"
   }


How to Use
==========

SublimeHg can be used in two ways:

- Through a menu-driven interface (command: ``hg``)
- Through a *command-line* interface (command: ``hg_cmd_line``)

Both systems ultimately talk to the new Mercurial command server; they only
differ in how you specify commands to it.

Normally, you will follow this steps:

#. Open the Command Palette (``Ctrl+Shift+P``) and look for ``SublimeHg``.
#. Select option
#. Select Mercurial command (or type in command line)

**Note:** Due to issues with input focus in widgets in Sublime Text 2080 and
lower, you might need to assign this commands their own key bindings in order
to make them work. They may not work from you from the Command Palette.


Bugs
====

- SublimeHg will fail to commit files with spaces in their paths. You can use
  wilcards instead from SublimeHg command-line interface to work around this.

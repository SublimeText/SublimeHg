=========
SublimeHG
=========

Issue commands to Mercurial from Sublime Text.


Requirements
============

* Mercurial 1.9 or above (command server)


Getting Started
===============

- Download and install `SublimeHG`_. (See `installation instructions`_ for ``.sublime-package`` files.)

.. _SublimeHG: https://bitbucket.org/guillermooo/downloads/sublimehg.sublime-package
.. _installation instructions: http://sublimetext.info/docs/en/extensibility/packages.html#installation-of-packages


Configuration
=============

By default, SublimeHG uses ``hg`` as the default executable name for Mercurial.
If you need to use a different one, like ``hg.bat``, set the variable
``packages.sublime_hg.hg_exe`` to it in your global settings (**Preferences | User Global Settings**).


How to Use
==========

SublimeHG offers two ways of using it:

- A menu-driven interface (``hg``)
- A command-line interface (``hg_command_line``)

Both systems ultimately use the new Mercrurial command server (Mercurial 1.9).
They only differ in how you issue commands to Mercurial.

To use SublimeHG:

#. Open de Command Palette (:kbd:`Ctrl+Shift+P`) and look for ``SublimeHG``.
#. Select option
#. Select Mercurial command or type in command line

Bugs
====

SublimeHG will fail to commit files with spaces in their paths. You can use
wilcards instead from the command-line interface to work around this.

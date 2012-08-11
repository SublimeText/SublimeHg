=========
SublimeHg
=========

Issue commands to Mercurial from Sublime Text.


Requirements
============

* Mercurial command server (Mercurial 1.9 or above)


Getting Started
===============

- `Download`_ and install SublimeHg. (See the `installation instructions`_ for *.sublime-package* files.)

.. _Download: https://bitbucket.org/guillermooo/sublimehg/downloads/SublimeHg.sublime-package
.. _installation instructions: http://docs.sublimetext.info/en/latest/extensibility/packages.html#installation-of-sublime-package-files


Configuration
=============

These options can be set in **Preferences | Settings - User**.

``packages.sublime_hg.hg_exe``

	By default, the executable name for Mercurial is ``hg``. If you need to
	use a different one, such as ``hg.bat``, change this option.

	Example::

	   {
	      "packages.sublime_hg.hg_exe": "hg.bat"
	   }

``packages.sublime_hg.terminal``

	Determines the terminal emulator to be used in Linux. Some commands, such
	as *serve*, need this information to work.

``packages.sublime_hg.extensions``

	A list of Mercurial extension names. Commands belonging to these extensions
	will show up in the SublimeHg quick panel along with built-in Mercurial
	commands.


How to Use
==========

SublimeHg can be used in two ways:

- Through a *menu* (``show_sublime_hg_menu`` command).
- Through a *command-line* interface (``show_sublime_hg_cli`` command).

Regardless of the method used, SublimeHg ultimately talks to the Mercurial
command server. The command-line interface is the more flexible option, but
some operations might be quicker through the menu.

By default, you have to follow these steps to use SublimeHg:

#. Open the Command Palette (``Ctrl+Shift+P``) and look for ``SublimeHg``.
#. Select option
#. Select Mercurial command (or type in command line)

It is however **recommended to assign** ``show_sublime_hg_cli`` and
``show_sublime_hg_menu`` their own **key bindings**.

For example::

	{ "keys": ["ctrl+k", "ctrl+k"], "command": "show_sublime_hg_menu" },
	{ "keys": ["ctrl+shift+k"], "command": "show_sublime_hg_cli" },


Restarting the Current Server
=============================

The Mercurial command server will not detect changes to the repository made
from the outside (perhaps from a command line) while it is running. To restart
the current server so that external changes are picked up, select
*Kill Current Server* from the command palette.

Tab Completion
==============

While in the command-line, top level commands will be autocompleted when you
press ``Tab``.


Quick Actions
=============

In some situations, you can perform quick actions.

Log
***

In a log report (*text.mercurial-log*), select two commit numbers (*keyword.other.changeset-ref.short.mercurial-log*)
and press *CTRL+ENTER* to **diff the two revisions** (*diff -rSMALLER_REV_NR:LARGER_REV_NR*).

If you want to **update to a revision number**, select a commit number and press *CTRL+SHIFT+ENTER* (*update REV_NO*).


Donations
=========

You can tip me through www.gittip.com: guillermooo_.

.. _guillermooo: http://www.gittip.com/guillermooo/
	
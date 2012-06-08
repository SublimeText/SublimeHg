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

.. _Download: https://bitbucket.org/guillermooo/sublimehg/downloads/SublimeHg.sublime-package
.. _installation instructions: http://sublimetext.info/docs/en/extensibility/packages.html#installation-of-packages


Configuration
=============

Available options in **Preferences | Settings - User**.

``packages.sublime_hg.hg_exe``

	By default, the executable name for Mercurial is ``hg``. If you need to
	use a different one, such as ``hg.bat``, change this option.
	``packages.sublime_hg.hg_exe`` to it in **Preferences | Global Settings -
	User**.

	Example::

	   {
	      "packages.sublime_hg.hg_exe": "hg.bat"
	   }

``packages.sublime_hg.terminal``

	Determines the terminal emulator to be used in Linux. This is necessary so
	that commands such as *serve* work.

``packages.sublime_hg.extensions``

	A list of Mercurial extension names. Commands belonging to these extensions
	will show up in the command menu along with built-in Mercurial commands.


How to Use
==========

SublimeHg can be used in two ways:

- Through a *menu*: ``show_sublime_hg_menu`` command.
- Through a *command-line* interface: ``show_sublime_hg_cli`` command.

Regardless of the method used to call it, SublimeHg ultimately talks to the
Mercurial command server. The command-line interface is the more flexible
option, but some operations might be quicker through the menu.

Normally, you will follow these steps to use SublimeHg:

#. Open the Command Palette (``Ctrl+Shift+P``) and look for ``SublimeHg``.
#. Select option
#. Select Mercurial command (or type in command line)

Alternatively, you can assign ``show_sublime_hg_cli`` and ``show_sublime_hg_menu``
their own key bindings.

Restarting The Current Server
-----------------------------

Sometimes you will need restart the current server so that external changes
to the repository are picked up. To do that, choose Kill Current Server from
the command palette.

.. # History
.. -------

.. Open the SublimeHg command line and type:

.. ``!h``
..    Displays history.

.. ``!mkh``
..    Persists current history between sessions.

Tab Completion
--------------

While in the command-line, top level commands will be autocompleted when you
press ``Tab``.

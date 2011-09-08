=========
SublimeHg
=========

Issue commands to Mercurial from Sublime Text.


Requirements
============

* Mercurial 1.9 or above (command server)


Getting Started
===============

- `Download`_ and install SublimeHg. (See `installation instructions`_ for
   ``.sublime-package`` files.)

.. _Download: https://bitbucket.org/guillermooo/sublimehg/downloads/SublimeHg.sublime-package
.. _installation instructions: http://sublimetext.info/docs/en/extensibility/packages.html#installation-of-packages


Configuration
=============

By default, SublimeHg uses ``hg`` as the default executable name for Mercurial.
If you need to use a different one, like ``hg.bat``, set the variable
``packages.sublime_hg.hg_exe`` to it in your global settings (**Preferences |
User Global Settings**).

Example::

   {
      "packages.sublime_hg.hg_exe": "hg.bat"
   }


How to Use
==========

SublimeHg can be used in two ways:

- Through a menu-driven interface (command: ``hg``)
- Through a *command-line* interface (command: ``hg_cmd_line``)

Both systems ultimately talk to the new Mercurial command server. The
command-line interface is more flexible than the other method.

Normally, you will follow these steps to use SublimeHg:

#. Open the Command Palette (``Ctrl+Shift+P``) and look for ``SublimeHg``.
#. Select option
#. Select Mercurial command (or type in command line)

Alternatively, you can assign the ``hg_command_line`` and ``hg`` commands their
own key bindings.

History
-------

Open the SublimeHg command line and type:

``!h``
   Displays history.

``!mkh``
   Persists current history between sessions.

Tab Completion
--------------

The command line will complete top level commands when you press :kbd:`Tab`.

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

By default, the executable name for Mercurial is ``hg``. If you need to use a
different one, such as ``hg.bat``, change the variable ``packages.sublime_hg.hg_exe``
to it in **Preferences | Global Settings - User**.

Example::

   {
      "packages.sublime_hg.hg_exe": "hg.bat"
   }


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


Known Issues
============

If you switch projects, ``default-push`` might be carried over inadvertently
from an unrelated repo. This should be inconvenient, but harmless. However,
you might conceivably carry over a ``default-push`` from a related repo and you
might end up pushing to the wrong repo. To solve this, always specify a
``default-push`` in your ``.hg/hgrc`` file.

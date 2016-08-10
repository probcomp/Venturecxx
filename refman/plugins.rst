.. _plugins-section:

Python Interface
----------------

The simplest way to invoke custom Python code from a toplevel
VentureScript program are the `pyexec` and `pyeval` inference actions
(which see).

For more elaborate integrations, one can write a plugin.  In a plugin,
one can

- Define callbacks

- Define foreign stochastic procedures for the inference language

- Define foreign stochastic procedures for the modeling language

- Manipulate Venture programmatically for any other purpose also

Plugins and Callbacks
=====================


A Venture `plugin` is just a Python module that defines a toplevel
function called ``__venture_start__``.

- To load a plugin when invoking Venture from the command line, pass
  ``-L <filename>``.

- To load a plugin when using Venture as a Python library,
  call ``ripl.load_plugin(filename)``.

- To load a plugin from a VentureScript inference program, use the
  ``load_plugin`` action (which see).

Any of these will load the plugin in the given file, and call its
``__venture_start__`` function with one argument, namely the Ripl
object representing the current Venture session.
The plugin is then free to invoke what methods it will on that Ripl.

If extra arguments are passed to either the ripl method
``load_plugin`` or the inference action ``load_plugin``, those will be
forwarded to the plugin's ``__venture_start__`` function.  If
``__venture_start__`` returns a value, that value will be returned by
``load_plugin``.  There is currently no way to pass arguments to a
plugin loaded from the command line, nor to capture any value that it
might return.

Useful ripl methods to call from a plugin's ``__venture_start__``:

- ``bind_callback(name, callable)`` to bind a given Python function as
  a call back that can be invoked with ``call_back`` (which see)

- ``bind_foreign_sp(name, SP)`` to bind a foreign stochastic procedure
  for the model language
  TODO: Document the stochastic procedure interface in this reference manual

- ``bind_foreign_inference_sp(name, SP)`` to bind a foreign stochastic
  procedure for the inference language
  TODO: Document the stochastic inference procedure interface in this reference manual

Built-in Callbacks
==================

.. include:: callbacks.gen

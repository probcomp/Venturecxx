Plugins and Callbacks
---------------------

The simplest way to invoke custom Python code from a toplevel Venture
program is to write a plugin and define some callbacks or Python SPs
in it.

A Venture `plugin` is just a Python module that defines a toplevel
function called ``__venture_start__``.

- To load a plugin when invoking Venture from the command line, pass
  ``-L <filename>``.

- To load a plugin when using Venture as a Python library,
  call ``ripl.load_plugin(filename)``.

Either will load the plugin in the given file, and call its
``__venture_start__`` function with one argument, namely the Ripl
object representing the current Venture session.
The plugin is then free to invoke what methods it will on that Ripl.

Useful ripl methods to call from a plugin's ``__venture_start__``:

- ``bind_callback(name, callable)`` to bind a given Python function as
  a call back that can be invoked with ``call_back`` and
  ``call_back_accum`` (which see)

- ``bind_foreign_sp(name, SP)`` to bind a foreign stochastic procedure
  for the model language
  TODO: Document the stochastic procedure interface in this reference manual

- ``bind_foreign_inference_sp(name, SP)`` to bind a foreign stochastic
  procedure for the inference language
  TODO: Document the stochastic inference procedure interface in this reference manual

After the ``__venture_start__`` function returns, initialization and
execution will continue (or, in the ``ripl.load_plugin`` case, the
``load_plugin`` method will return).

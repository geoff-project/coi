Problem Registry
================

This package provides an *registry* similar to the one provided by Gym itself.
Every optimization problem that wants to be usable in a generic context should
register itself to it. The usage is as follows:

.. code-block:: python

    from cernml.coi import OptEnv, register

    class MyEnv(OptEnv):
        ...

    register('mypackage:MyEnv-v0', entry_point=MyEnv)

This makes your environment known to "the world" and an environment management
application that imports your package knows how to find and interact with your
environment.

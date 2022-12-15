# Configuration of Problems

```{eval-rst}
.. autoclass:: cernml.coi.Configurable
    :show-inheritance:

    .. automethod:: get_config
    .. automethod:: apply_config

.. autoclass:: cernml.coi.Config
    :show-inheritance:

    .. automethod:: add
    .. automethod:: extend
    .. automethod:: validate
    .. automethod:: validate_all
    .. automethod:: fields
    .. automethod:: get_field_values
    .. autoclass:: cernml.coi.Config.Field
        :members:
        :show-inheritance:

.. autoclass:: cernml.coi.ConfigValues

.. autoexception:: cernml.coi.BadConfig

.. autoexception:: cernml.coi.DuplicateConfig
```

.. SPDX-FileCopyrightText: 2020 - 2024 CERN
.. SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
.. SPDX-FileNotice: All rights not expressly granted are reserved.
..
.. SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

:tocdepth: 3

The Internal Machinery
======================

.. automodule:: cernml.coi._machinery
    :no-members:

Further Reading
---------------

- :ref:`std:Metaclasses` in the `Python documentation`_
- `abc.ABCMeta`
- `typing.Protocol` and `typing.runtime_checkable`
- `Protocols and structural subtyping`_ in the Python `Type System Reference`_
- Protocols_ in the `Specification for the Python type system`_

.. _`Python documentation`:
   https://docs.python.org/3/index.html
.. _Protocols and structural subtyping:
   https://typing.readthedocs.io/en/latest/source/protocols.html
.. _Type System Reference:
   https://typing.readthedocs.io/en/latest/source/reference.html
.. _Protocols:
   https://typing.readthedocs.io/en/latest/spec/protocol.html
.. _Specification for the Python type system:
   https://typing.readthedocs.io/en/latest/spec/index.html

Classes Provided by This Module
-------------------------------

These classes present the public-facing API of this private module.

.. autoclass:: AttrCheckProtocol
    :special-members: __subclasshook__
.. autoclass:: AttrCheckProtocolMeta
    :special-members: __new__, __init__, __instancecheck__, __subclasscheck__,
       __dir__

Attribute-Matching Logic
------------------------

These functions implement the core logic of `AttrCheckProtocol`.

.. autofunction:: attrs_match
.. autofunction:: find_mismatched_attr
.. autofunction:: is_protocol
.. autofunction:: attr_in_annotations

Compatibility Shims
-------------------

These functions exist to provide compatibility between all Python versions from
3.9 to 3.12.

.. autofunction:: non_callable_proto_members
.. autofunction:: proto_classmethods
.. autofunction:: protocol_attrs
.. autodata:: _SPECIAL_NAMES

Utilities and Dark Magic
------------------------

The following section documents a few “tricks” that have been used in this
module. It also documents the behavior of several internal items of the
`typing` module, as they have been observed in the Python versions from 3.9 to
3.12.

.. autoclass:: typing._ProtocolMeta

    This metaclass implements the behavior of `Protocol`. Our class
    `.AttrCheckProtocolMeta` largely copies it and overrides its behavior where
    necessary.

    .. method:: __new__(mcs, name: str, bases: tuple[type, ...], namespace: dict[str, typing.Any], /, **kwargs: typing.Any) -> _ProtocolMeta
        :staticmethod:

        Constructor for new classes of this metaclass.

        This is called by `.AttrCheckProtocolMeta.__new__()`. It validates the
        *bases* of the new class. If one of the bases is `Protocol` (determined
        by :samp:`if Procol in {bases}`), *all* bases must be protocols
        (as determined by `.is_protocol()`) or be on a special allow-list of
        standard-library ABCs.

        Note that `.AttrCheckProtocolMeta` always forces this test to run, even
        if `Protocol` is not among the direct bases of the new class.

    .. method:: __instancecheck__(instance: typing.Any) -> bool

        This method is very similar to
        `.AttrCheckProtocolMeta.__instancecheck__()`. It guards against three
        cases and has one fallback:

        1. For `Protocol` itself, the default instance check is executed.
        2. For concrete subclasses, it defers to :ref:`api/machinery:the
           instance check of ABCMeta`.
        3. For (runtime) protocols, it first runs :ref:`api/machinery:the
           instance check of ABCMeta`.
        4. Only if that fails does it compare attributes between the protocol
           and the instance.

    .. method:: __subclasscheck__(other: type) -> bool

        This method is similar in complexity to `__instancecheck__()`. It
        guards against four edge cases and has one fallback:

        1. If the owner is `Protocol` itself, defer to the default subclass
           check, which only considers inheritance.
        2. If the owner is a concrete subclass, just run the subclass check of
           `~abc.ABCMeta`.
        3. Now we know the owner is a protocol. Raise an exception if *other*
           isn't a type or if the owner isn't a *runtime* protocol.
        4. Also raise an exception if the owner is a runtime protocol with
           non-callable members [#rtp]_ and its
           :meth:`~abc.ABCMeta.__subclasshook__()` isn't overridden. This case
           never triggers for `.AttrCheckProtocol` because it *always*
           overrides the `~.AttrCheckProtocol.__subclasshook__()`.
        5. If the above checks don't raise an exception, just defer to
           `~abc.ABCMeta` like in case 2. This checks inheritance and virtual
           subclassing and eventually runs our
           `~.AttrCheckProtocol.__subclasshook__()`, which will call
           `.attrs_match()`.

.. function:: typing._get_protocol_attrs(cls: typing._ProtocolMeta) -> set[str]

    Collect protocol members from a class and all its bases.

    This function iterates through a protocol class's :term:`method resolution
    order` and collects all :term:`attributes <attribute>` (both callable and
    non-callable) and :term:`variable annotations <variable annotation>`. The
    former are accessed via `~object.__dict__`, the latter via
    `~function.__annotations__`.

    There are two notable exceptions:

    1. The classes `Protocol`, `Generic` and `object` are not inspected for
       members (But `AttrCheckProtocol` unfortunately is).
    2. Names that are on a fixed disallow-list are never added as members. This
       includes implementation details of `abc`, certain magic methods, and all
       magic attributes defined by `typing`. It does *not* include
       `.__proto_classmethods__`, which is why we have to remove it manually.

    Starting with Python 3.12, this function is called once during class
    creation. On older Python versions, `Protocol` calls it on every instance
    or subclass check.

    This function is private, but has been unmodified at least from Python 3.9
    to 3.12.

.. data:: typing._proto_hook
    :value: <classmethod(<function _proto_hook>)>

    This function is inserted as a :meth:`~abc.ABCMeta.__subclasshook__()` into
    every protocol class. It checks if the owning class is a protocol and, if
    yes, determines whether the given subclass implements all protocol members.

    This module does not use this function at all. We always override it with
    our own `~AttrCheckProtocol.__subclasshook__()`.

.. autofunction:: lazy_load_getattr_static

.. function:: _get_dunder_dict_of_class(obj: type) -> dict[str, object]

    Safely access a type's attribute mapping.

    This is the :term:`descriptor` method :meth:`~object.__get__()` bound to
    the descriptor `type.__dict__ <object.__dict__>`. Binding it this way
    ensures that:

    1. it can only be called on `type` objects;
    2. it cannot be overridden by subclasses or metaclasses.

    This is how `protocol_attrs()` and its siblings access
    `.__protocol_attrs__` and its related attributes on a protocol class
    without also looking them up in the bases of that class.

.. function:: _static_mro(obj: type, /) -> tuple[type, ...]

    Safely access a type's :term:`method resolution order`.

    This is the :term:`descriptor` method :meth:`~object.__get__()` bound to
    the descriptor `type.__mro__`. Binding it this way ensures that:

    1. it can only be called on `type` objects;
    2. it cannot be overridden by subclass or metaclass descriptors.

    This way, we can iterate all direct and indirect bases of a `type` object.

.. function:: get_class_annotations(obj: type, /) -> dict[str, object]

    Safely access a type's :term:`variable annotation` mapping.

    On Python 3.10+, this is simply the :term:`descriptor` method
    :meth:`~object.__get__()` bound to the descriptor `type.__annotations__
    <function.__annotations__>`.
    Binding it this way ensures that:

    1. it can only be called on `type` objects;
    2. it cannot be overridden by subclass or metaclass descriptors.

    On Python version 3.9 and lower, this is `get_class_annotations_impl()`,
    which serves as a compatibility shim.

.. autofunction:: get_class_annotations_impl

.. function:: _GetAttr(obj: object, name: str, default: t.Optional[typing.Any] = ..., /) -> typing.Any

    The call signature of :func:`~inspect.getattr_static()`. This is used as
    type annotation for the return value of `lazy_load_getattr_static()`.

.. autoclass:: _AlwaysContainsProtocol

The Instance Check of ABCMeta
-----------------------------

The instance check of `~abc.ABCMeta` (and, in fact, the built-in
:func:`isinstance()` check as well) tests whether *at least one* of
:samp:`type({obj})` *and* :samp:`{obj}.__class__` is a subclass of the ABC,
since the two may be different. This is e.g. the case for `Mock
<unittest.mock.Mock.__class__>`.

.. code-block:: python

    >>> class Bystander:
    ...     pass
    ...
    >>> class Mocker:
    ...     __class__ = Bystander
    ...
    >>> mocker = Mocker()
    >>> type(mocker)
    <class '__main__.Mocker'>
    >>> mocker.__class__
    <class '__main__.Bystander'>
    >>> isinstance(mocker, Mocker)
    True
    >>> isinstance(mocker, Bystander)
    True

The subclass check of `~abc.ABCMeta` (which the instance check uses) is
recursive: Whenever you ask whether ``A`` is a subclass of ``B``, the check
asks ``B`` **and all subclasses** of ``B``. These subclasses include real
subclasses (via :meth:`type.__subclasses__()`) and virtual subclasses (via
:meth:`~abc.ABCMeta.register()`). This means that any particular magic
implemented in this package must be careful not to cause infinite recursion
when running subclass checks within their own hooks.

The Subclass Hook of the Core Classes
-------------------------------------

The :doc:`classes` (which are :term:`ABCs <abstract base class>`, but not
`Protocol`\ s) also define a :meth:`~abc.ABCMeta.__subclasshook__()`. This hook
only applies to these classes themselves and not to any subclasses.

The hook of each ABC runs the subclass check of its corresponding
:doc:`protocol <protocols>` and reports True on success. That means that
anything is a subclass of one of the protocols is also a subclass of the ABC:

.. code-block:: python

    >>> from cernml import coi
    ...
    >>> class Sub(coi.protocols.Problem):
    ...     pass
    ...
    >>> issubclass(Sub, coi.Problem)
    True

The reason for this behavior is that previous versions of this package used to
suggest :samp:`isinstance({obj}, {ABC})` as check whether an object implemented
one of the protocols, whereas the :doc:`protocol classes <protocols>` didn't
exist yet. This preserves the old semantics while giving people time to
transition to the :doc:`typeguards`.

There is one more trick to the hooks described here: They not only guard
against being invoked by subclasses, but also against being used to check their
respective protocol class:

.. code-block:: python

   >>> coi.Problem.__subclasshook__(coi.protocols.Problem)
   NotImplemented
   >>> issubclass(coi.protocols.Problem, coi.Problem)
   False

`~abc.ABCMeta` runs this check when we register the ABCs as subclasses of the
protocols to prevent cyclic inheritance. But the check happens when the ABCs
themselves aren't bound to their names yet, so we must be careful to only use
their names after making this check.

The Implementation of Intersection Protocols
--------------------------------------------

Normally, an `intersection protocol`_ is simply a protocol that inherits from
two or more other protocols:

    >>> from cernml.coi._machinery import is_protocol
    >>> from collections.abc import Container, Sized
    >>> from typing import Protocol, runtime_checkable
    ...
    >>> @runtime_checkable
    ... class SizedContainer(Sized, Container, Protocol):
    ...     pass
    ...
    >>> class Empty:
    ...     def __contains__(self, x):
    ...         return False
    ...
    ...     def __len__(self):
    ...         return 0
    ...
    >>> is_protocol(SizedContainer)
    True
    >>> issubclass(Empty, SizedContainer)
    True

Our own :doc:`intersections` cannot rely on this trivial behavior. Since they
subclass `~gymnasium.Env`, which isn't a `Protocol`, they are not proper
protocols themselves (and static type checkers recognize this).

To circumvent this issue, they manually mark themselves as runtime protocols,
setting both `~AttrCheckProtocol._is_protocol` and
`~AttrCheckProtocol._is_runtime_protocol`. They also call
`non_callable_proto_members()` once to set
`~AttrCheckProtocol.__non_callable_proto_members__`. On Python 3.12+, this
attribute would usually be setby `runtime_checkable`. While we generally use
this attribute lazily, there is one location in `_ProtocolMeta` that expects
the attribute to exist on Python 3.12+.

Finally, the intersection protocols also override
`AttrCheckProtocol.__subclasshook__()`. In the override, they check whether
their respective `~gymnasium.Env` subclass appears in the subclass's
:term:`MRO` and return a flat False if not. Otherwise, they simply forward to
their parent.

Without this additional check, we would treat the underlying environment class
as if it were a protocol. Consequently, the intersections
`.SeparableOptGoalEnv` and `.SeparableOptEnv` would be identical because they
expect exactly the same set of attributes and methods. However, the semantics
of `GoalEnv.compute_reward() <gymnasium_robotics.core.GoalEnv.compute_reward>`
and `SeparableEnv.compute_reward() <cernml.coi.SeparableEnv.compute_reward>`
differs considerably and they expect different arguments. Thus, there's still
value in distinguishing the two. (And this is also what previous versions of
this package did.)

.. _intersection protocol:
    https://typing.readthedocs.io/en/latest/spec/protocol.html
    #unions-and-intersections-of-protocols

.. [#rtp]
   Runtime protocols with data members are fine for :func:`isinstance()`
   checks but not for :func:`issubclass` checks.

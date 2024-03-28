..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

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
        2. For concrete subclasses, it defers to the instance check of
           `~abc.ABCMeta` [#typeclass]_.
        3. For (runtime) protocols, it first runs the instance check of
           `~abc.ABCMeta` [#typeclass]_.
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
    the descriptor `type.__mro__ <class.__mro__>`. Binding it this way ensures
    that:

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

.. [#rtp]
   Runtime protocols with data members are fine for :func:`isinstance()`
   checks but not for :func:`issubclass` checks.

.. [#typeclass]
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
        >>> assert type(mocker) is Mocker
        >>> assert mocker.__class__ is Bystander
        >>> assert isinstance(mocker, Mocker)
        >>> assert isinstance(mocker, Bystander)

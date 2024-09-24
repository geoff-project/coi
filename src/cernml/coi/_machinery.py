# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# You know some real FUN is going to happen!
# pylint: disable = import-outside-toplevel
# pylint: disable = protected-access
# pylint: disable = unsupported-membership-test

"""The dimly lit machine room of the COI.

The :doc:`classes` all share the same special behavior: they can be
superclasses of other classes even if those other classes don't directly
inherit from them. All that is necessary is that those classes provide
certain members as determined by the core class in question. Crucially,
this check works at runtime and takes into account whether a member is
a regular attribute, a method or a `classmethod`.

The core classes don't implement this check themselves. Instead, they
rely on a number of pure, stateless protocols, one for each of the core
classes. These :doc:`protocols` are based on the standard-library
features `typing.Protocol` and `typing.runtime_checkable`. However, the
standard library prohibits runtime checks for non-method members, which
our classes all do.

Our protocols allow this because our protocols are a special kind of
protocols. They inherit from `AttrCheckProtocol`, a subclass of
`Protocol` that extends runtime checks with the above two capabilities.
The purpose of this page is to describe how exactly this extension has
been implemented.

The first section documents the :ref:`api/machinery:Classes Provided by
This Module` as a public API of this private module. The following
section describes the :ref:`api/machinery:Attribute-Matching Logic` in
detail. After this, several :ref:`api/machinery:Compatibility Shims` are
described that ensure that this module works on all Python versions
starting from 3.9. Following this, :ref:`api/machinery:Utilities and
Dark Magic` documents a few particularly obscure hacks. Finally, we
conclude with notes on various tricky implementation details surrounding
:ref:`api/machinery:The Instance Check of ABCMeta`,
:ref:`api/machinery:The Subclass Hook of the Core Classes`, and
:ref:`api/machinery:The Implementation of Intersection Protocols`.
"""

import functools
import typing as t
from abc import ABCMeta
from collections.abc import Mapping
from types import GetSetDescriptorType

if t.TYPE_CHECKING:
    from typing_extensions import TypeGuard

__all__ = (
    "AttrCheckProtocol",
    "AttrCheckProtocolMeta",
    "attr_in_annotations",
    "attrs_match",
    "find_mismatched_attr",
    "get_class_annotations",
    "get_class_annotations_impl",
    "get_dunder_dict_of_class",
    "get_static_mro",
    "is_protocol",
    "lazy_load_getattr_static",
    "non_callable_proto_members",
    "proto_classmethods",
    "proto_hook",
    "protocol_attrs",
)


get_static_mro: t.Callable[[type], tuple[type, ...]] = vars(type)["__mro__"].__get__
get_dunder_dict_of_class: t.Callable[[type], dict[str, object]] = vars(type)[
    "__dict__"
].__get__


def get_class_annotations_impl(obj: type, /) -> dict[str, object]:
    """Safely retrieve annotations from a type object.

    This is copied from :func:`inspect.get_annotations()` for backwards
    compatibility with Python 3.9. The following changes have been made:

    - remove logic for non-type objects;
    - remove logic for evaluation of annotations;
    - replace unsafe :func:`getattr()` with access via the
      `~object.__dict__` descriptor;
    - whereas :func:`inspect.get_annotations()` never modifies *obj* and
      always returns a fresh `dict`, this function only creates a new
      `dict` if necessary, and also assigns it to
      :samp:`{obj}.__annotations__` in that case. This is to be parallel
      with the Python 3.10 :doc:`data descriptor for annotations
      <std:howto/annotations>`.

    If the dict cannot be assigned (e.g. because *obj* is a builtin
    type), this function raises an `AttributeError` error, again to be
    compatible with the data descriptor introduced in Python 3.10.

    This function is normally called as `get_class_annotations()` and
    only used on Python 3.9. Under this name, however, it is available
    on all versions. This is for documentation and testing purposes.
    """
    obj_dict = get_dunder_dict_of_class(obj)
    ann = obj_dict.get("__annotations__", None)
    if isinstance(ann, GetSetDescriptorType):
        # This is the case e.g. when `obj` is `types.FunctionType`.
        ann = None
    if ann is None:
        ann = {}
        try:
            type.__setattr__(obj, "__annotations__", ann)
        except TypeError:
            # Compatibility with built-in `type.__annotations__`.
            raise AttributeError(
                f"{obj.__class__.__name__} object {obj.__name__!r} "
                f"has no attribute '__annotations__'"
            ) from None
        return ann
    return t.cast(dict, ann)


try:  # pragma: no cover
    get_class_annotations: t.Callable[[type], dict[str, object]] = vars(type)[
        "__annotations__"
    ].__get__
except KeyError:  # pragma: no cover
    get_class_annotations = get_class_annotations_impl


class _AlwaysContainsProtocol(tuple):
    """Hack to force base-class checks in `~typing._ProtocolMeta`.

    This is a simple subclass of `tuple`. Its only custom behavior is
    that :meth:`~object.__contains__()` always returns True for `Protocol`.
    See `AttrCheckProtocolMeta.__new__()` for why we need this behavior.
    """

    __slots__ = ()

    def __contains__(self, obj: object, /) -> bool:
        return obj is t.Protocol or super().__contains__(obj)


class AttrCheckProtocolMeta(t._ProtocolMeta):
    """The metaclass of `AttrCheckProtocol`.

    This contains the bulk of the injection logic that we use to
    override the standard behavior of protocols. The logic that checks
    whether a class implements a protocol is in `attrs_match()`.

    See the chapter :ref:`std:Metaclasses` of the Python documentation
    for details on class creation.
    """

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, t.Any],
        /,
        **kwargs: t.Any,
    ) -> "AttrCheckProtocolMeta":
        """Constructor for new classes of this metaclass.

        This is just about the earliest point during class creation.
        (The only things that run even earlier would be
        ``__prepare__()``, which we don't define; and the constructor of
        any sub-metaclass.)

        This method overrides `~AttrCheckProtocol.__init_subclass__()`
        with custom values by injecting them directly into the
        *namespace* as follows:

        - `~AttrCheckProtocol._is_protocol` is set to True if
          `AttrCheckProtocol` is a direct base of the new class. If this
          isn't the case, the original check still runs later. If the
          flag is already True, we don't modify it again.
        - `~AttrCheckProtocol.__subclasshook__()` is set to our own
          implementation unless a custom hook has already been set.

        We supply these values here because
        `~AttrCheckProtocol.__init_subclass__()` is called as part of
        :class:`type.__new__() <type>`, which is called by this method.
        We cannot override `~AttrCheckProtocol.__init_subclass__()`
        because `typing._get_protocol_attrs()` would pick up the
        override as a protocol method.

        If the new class is a protocol, this metaclass also wraps
        *bases* in an `_AlwaysContainsProtocol`. This forces
        `~typing._ProtocolMeta` to run its base-class check, even if
        `Protocol` is not a direct base of the new class. At the same
        time, this does not change the *actual* bases of the new class.
        """
        if name == "AttrCheckProtocol" and bases == (t.Protocol,):
            namespace["_is_protocol"] = True
            namespace["_is_runtime_protocol"] = False
        elif not namespace.get("_is_protocol", False):
            is_protocol = any(b is AttrCheckProtocol for b in bases)
            namespace["_is_protocol"] = is_protocol
            if is_protocol:
                if not isinstance(bases, tuple):
                    raise TypeError(
                        f"type.__new__() argument 2 must be tuple, "
                        f"not {bases.__class__.__name__}"
                    )
                bases = _AlwaysContainsProtocol(bases)
        namespace.setdefault("__subclasshook__", proto_hook)
        return super().__new__(mcs, name, bases, namespace, **kwargs)

    def __init__(cls, *args: t.Any, **kwargs: t.Any) -> None:
        """Initializer for new classes of this metaclass.

        The initializer runs after `__new__()` and thus also after
        `~AttrCheckProtocol.__init_subclass__()`. The implementation of
        `_ProtocolMeta` uses it to set
        `~AttrCheckProtocol.__protocol_attrs__` on Python versions
        3.12+. Our implementation creates it on all Python versions.

        If the attribute has been set by `_ProtocolMeta`, this metaclass
        uses the opportunity to remove any `_SPECIAL_NAMES` that might
        have been picked up. Because this happens before
        `runtime_checkable` has run, these special names don't appear in
        `~AttrCheckProtocol.__non_callable_proto_members__` either.
        """
        super().__init__(*args, **kwargs)
        if getattr(cls, "_is_protocol", False):
            # Annotate here, not in class scope, to keep __annotations__
            # clean.
            cls.__protocol_attrs__: set[str]  # noqa: B032
            if "__protocol_attrs__" in vars(cls):
                # Python 3.11 and above.
                cls.__protocol_attrs__ -= _SPECIAL_NAMES
            else:
                # Python 3.10 and lower.
                cls.__protocol_attrs__ = protocol_attrs(cls)

    def __instancecheck__(cls, instance: t.Any) -> bool:
        """Overload for :func:`isinstance()`.

        This is the entry point on any instance check. It is also the
        first point where we don't just extend the behavior of
        `Protocol`, but overwrite it. We generally don't want to invoke
        its logic since it would generally raise an exception on our
        protocols.

        We guard against three special cases and have one fallback,
        adding up to four branches total. None of the branches must lead
        to the attribute-checking logic of `Protocol`.

        1. If the call is :samp:`isinstance({obj}, AttrCheckProtocol)`),
           we ignore all overloads and defer to the default
           implementation of :meth:`class.__instancecheck__()`, which
           only regards regular subclassing.

        2. If this gets called via a concrete class, we defer to
           :ref:`api/machinery:the instance check of ABCMeta`. We could
           defer to our direct superclass `_ProtocolMeta` since it would
           lead to the same result; however, we *must* skip it in the
           following case, so we might as well maintain symmetry between
           both cases.

        3. If this wasn't called on `AttrCheckProtocol` itself nor on
           a concrete class, it must've been called on a protocol class.
           Run :ref:`api/machinery:the instance check of ABCMeta`. This
           covers subclasses via inheritance and via
           :meth:`~abc.ABCMeta.register()`. Unless the result is cached,
           this will run our `__subclasscheck__()`.

        4. Only if that check fails do we check the attributes via
           `attrs_match()`. We want to do this last because it's the
           slowest test by far.

        Raises:
            `TypeError`: if called on a protocol class that isn't
                `runtime_checkable`.
        """
        if cls is AttrCheckProtocol:
            return type.__instancecheck__(cls, instance)
        if not getattr(cls, "_is_protocol", False):
            # Our cls is not a protocol, it's a concrete subclass of
            # a protocol. Run the ABC instance check. We could call
            # `super()` here, but that would lead to the same result.
            return ABCMeta.__instancecheck__(cls, instance)
        if not getattr(cls, "_is_runtime_protocol", False):
            raise TypeError(
                "Instance and class checks can only be used with"
                " @runtime_checkable protocols"
            )
        # Skip _ProtocolMeta.__instancecheck__, it runs through the
        # attribute list with the primitive test we want to avoid.
        if ABCMeta.__instancecheck__(cls, instance):
            return True
        return attrs_match(cls, instance)

    def __subclasscheck__(cls, other: type) -> bool:
        """Overload for :func:`issubclass()`.

        Unlike `__instancecheck__()`, this override is very simple,
        since the bulk of the logic happens in our
        `~AttrCheckProtocol.__subclasshook__()`. We simply ensure that
        `AttrCheckProtocol` gets the same special treatment as
        `Protocol` (i.e. the default check runs, no virtual
        subclassing). Otherwise, we simply call the original
        `~typing._ProtocolMeta.__subclasscheck__()`. This is possible
        because it ensures not to ignore our custom subclass hook.
        """
        if cls is AttrCheckProtocol:
            return type.__subclasscheck__(cls, other)
        return super().__subclasscheck__(other)

    def __dir__(cls) -> t.Iterable[str]:
        """Override for :func:`dir()`.

        This simply adds `~AttrCheckProtocol.__protocol_attrs__` to the
        attributes found by the default implementation. This is
        necessary so that :meth:`~unittest.mock.Mock.mock_add_spec()`
        mocks not only regular protocol members, but also those defined
        as a :term:`variable annotation`.
        """
        # Include protocol members that only exist as annotations.
        # Without this. `unittest.Mock()` won't be able to auto-spec
        # these members
        attrs = super().__dir__()
        annotations = set(cls.__protocol_attrs__)
        return sorted(set(attrs) | annotations)


@classmethod  # type: ignore[misc]
def proto_hook(cls: AttrCheckProtocolMeta, other: type) -> t.Any:
    """The subclasshook for all attribute-checking protocols.

    This is actually defined outside of the class as ``proto_hook()``.
    It is injected by `AttrCheckProtocolMeta.__new__()` and prevents
    `Protocol` from injecting its own `typing._proto_hook`.

    This method is ultimately responsible for implementing the protocol
    logic for :func:`issubclass()`. It first checks whether the owning
    class is a protocol (using `_is_protocol`) and gives up if not. This
    prevents us from overriding the subclassing behavior of concrete
    subclasses.

    It then uses `attrs_match()` to determine if the other class is
    compatible with the owning protocol. If yes, the other class is
    a subclass. If not, we return `NotImplemented` (rather than False)
    to let `~abc.ABCMeta` search the registered subclasses of the
    protocol.
    """
    # pylint: disable = protected-access
    if not cls.__dict__.get("_is_protocol", False):
        return NotImplemented
    # No need to check for `isinstance(other, type)` at this point; on
    # Python 3.12 this is done in `_ProtocolMeta.__subclasscheck__()`.
    # On older versions, it is done in `ABCMeta.__subclasscheck__()`.
    # if not isinstance(other, type):
    #     # Same error message as for issubclass(1, int).
    #     raise TypeError("issubclass() arg 1 must be a class")
    if not attrs_match(cls, other):
        return NotImplemented
    return True


def attrs_match(proto: AttrCheckProtocolMeta, obj: object) -> bool:
    """Check if the attributes of *obj* match those of *proto*.

    This is the core logic of `AttrCheckProtocol`, called by both
    :func:`isinstance()` and :func:`issubclass()`. It iterates over all
    protocol members (which have been cached at class creation) and
    attempts to access each one on *obj* via
    :func:`~inspect.getattr_static()`.

    If *obj* is itself a protocol (determined by `is_protocol()`),
    its annotations (and those of its base classes) are checked as well.
    This is done via `attr_in_annotations()`.

    If the protocol member is a `classmethod` (determined by
    `proto_classmethods()`), we only look it up on *obj* if *obj* is
    a type. If it isn't a type, we look it up on :samp:`type({obj})`. We
    *don't* use `~instance.__class__` because `type` is what is used in
    the :term:`method resolution order`. (See :ref:`api/machinery:the
    instance check of ABCMeta`.)

    If the attribute is found on *obj*, further tests depend on the
    nature of the protocol member:

    - If it's a method (determined by `non_callable_proto_members()`),
      the attribute may be any object except `None`.
    - If it's a `classmethod` (determined by `proto_classmethods()`),
      the attribute must be a class method as well.
    - Otherwise, the attribute may be any object.
    """
    return find_mismatched_attr(proto, obj) is None


def find_mismatched_attr(proto: AttrCheckProtocolMeta, obj: object) -> t.Optional[str]:
    """Return the name of the first mismatched attribute.

    This is the actual implementation of `attrs_match()`. If an
    instance/subclass check unexpectedly fails, a user may call this
    function manually to find the name of the offending protocol member.
    """
    getattr_static = lazy_load_getattr_static()
    for attr in protocol_attrs(proto):
        is_classmethod = attr in proto_classmethods(proto)
        try:
            val = getattr_static(
                type(obj) if is_classmethod and not isinstance(obj, type) else obj, attr
            )
        except AttributeError:
            if not (is_protocol(obj) and attr_in_annotations(obj, attr)):
                return attr
        else:
            if is_classmethod:
                if not isinstance(val, classmethod):
                    return attr
            elif val is None and attr not in non_callable_proto_members(proto):
                return attr
    return None


def is_protocol(obj: object) -> "TypeGuard[AttrCheckProtocolMeta]":
    """Check whether *obj* is `Protocol` or a subclass of it.

    This simply reads the flag `~AttrCheckProtocol._is_protocol`, but
    also requires *obj* to be a type and a subclass of `Generic`, as
    a safety measure.

    This has been copied from Python 3.12 `typing._proto_hook()` and
    `_ProtocolMeta.__new__() <typing._ProtocolMeta.__new__>`.
    """
    return (
        isinstance(obj, type)
        and issubclass(obj, t.Generic)  # type: ignore[arg-type]
        and getattr(obj, "_is_protocol", False)
    )


def attr_in_annotations(proto: AttrCheckProtocolMeta, attr: str) -> bool:
    """Check if *proto* or anything in its :term:`MRO` annotate *attr*.

    This check is necessary because protocols are allowed to define
    members by a :term:`variable annotation` without providing a value.
    Such annotations cannot be found by
    :func:`~inspect.getattr_static()`.

    This code is modified from Python 3.12 `typing._proto_hook()`.
    """
    for base in get_static_mro(proto):
        try:
            annotations = get_class_annotations(base)
        except AttributeError:
            continue
        if isinstance(annotations, Mapping) and attr in annotations:
            return True
    return False


def non_callable_proto_members(cls: AttrCheckProtocolMeta) -> set[str]:
    """Lazy collection of any protocol members that aren't methods.

    If the attribute `.__non_callable_proto_members__` already exists,
    return it immediately. Otherwise, create and return it as a subset of
    `.__protocol_attrs__`.

    In Python 3.12+, the attribute is created by `runtime_checkable`. On
    all older versions, this function creates it on first use.

    Class methods are not included in this collection. This is so that
    they can be explicitly deleted by being assigned None, just like for
    regular methods.

    `classmethod` objects are a bit weird; on their own, they are *not*
    callable. However, we fetch them here via :samp:`getattr({cls},
    {name})`. Because they are :term:`descriptors <descriptor>`, this
    calls :samp:`{the_classmethod}.__get__(None, {cls})`, which binds
    them to the class. The bound-method object thus returned *is*
    callable.

    This code is modified from Python 3.12 `runtime_checkable`.
    """
    # Don't use `getattr()` to avoid lookup in super classes.
    members = t.cast(
        t.Union[set[str], None],
        get_dunder_dict_of_class(cls).get("__non_callable_proto_members__"),
    )
    if members is None:
        members = set()
        for attr in protocol_attrs(cls):
            try:
                # Using `getattr` here serves two purposes: 1. it binds
                # classmethods, making them callable, and 2. it
                # automatically looks up attributes in parent protocols.
                is_callable = callable(getattr(cls, attr, None))
            except Exception as e:
                raise TypeError(
                    f"Failed to determine whether protocol member {attr!r} "
                    f"is a method member"
                ) from e
            if not is_callable:
                members.add(attr)
        cls.__non_callable_proto_members__ = members  # type: ignore[attr-defined]
    return members


def proto_classmethods(cls: AttrCheckProtocolMeta) -> set[str]:
    """Lazy collection of any protocol class methods.

    If the attribute `.__proto_classmethods__` already exists, return it
    immediately. Otherwise, create and return it as a subset of
    `.__protocol_attrs__`.

    Whether an object is a class method is tested by
    :samp:`isinstance({attr}, classmethod)`. Note that at least on
    CPython, this is true even for implicit class methods like
    :meth:`~object.__init_subclass__()` and
    :meth:`~object.__class_getitem__()`.

    The logic in this function follows that of
    `non_callable_proto_members()`.
    """
    # Don't use `getattr()` to avoid lookup in super classes.
    members = t.cast(
        t.Union[set[str], None],
        get_dunder_dict_of_class(cls).get("__proto_classmethods__"),
    )
    if members is None:
        # Access the attributes via the class dictionary; access
        # via `getattr()` would bind them and give us bound-method
        # objects, not classmethod objects!
        cvars = get_dunder_dict_of_class(cls)
        members = set()
        for attr in protocol_attrs(cls):
            try:
                is_classmethod = isinstance(cvars.get(attr, None), classmethod)
            except Exception as e:
                raise TypeError(
                    f"Failed to determine whether protocol member {attr!r} "
                    f"is a classmethod member"
                ) from e
            if is_classmethod:
                members.add(attr)
        cls.__proto_classmethods__ = members  # type: ignore[attr-defined]
    return members


# Extension of the `typing` exclusion list with our own attributes.
_SPECIAL_NAMES: set[str] = {
    "__protocol_attrs__",
    "__non_callable_proto_members__",
    "__proto_classmethods__",
}
"""This is the collection of magic attributes that we treat specially
*in addition* to those that `typing` defines. This is used by
`protocol_attrs()` and `AttrCheckProtocolMeta.__init__()` to ensure that
these attributes don't appear as part of any protocols."""


def protocol_attrs(cls: type) -> set[str]:
    """Lazy collection of any protocol attributes.

    If a protocol has an attribute `.__protocol_attrs__`, return it
    immediately. Otherwise, call the private function
    `typing._get_protocol_attrs()`. Modify its return value to exclude
    our magic attributes, as documented under `_SPECIAL_NAMES`.

    Note that unlike `non_callable_proto_members()` and
    `proto_classmethods()`, this function *never* caches its result.
    This is done in `AttrCheckProtocolMeta.__init__()` instead.
    """
    # Don't use `getattr()` to avoid lookup in super classes.
    attrs = t.cast(
        t.Union[set[str], None],
        get_dunder_dict_of_class(cls).get("__protocol_attrs__"),
    )
    if attrs is not None:
        return attrs
    attrs = t._get_protocol_attrs(cls)  # type: ignore[attr-defined]
    attrs.difference_update(_SPECIAL_NAMES)
    return attrs


class _GetAttr(t.Protocol):  # pragma: no cover
    """The call signature of `getattr_static()`."""

    def __call__(
        self, obj: object, name: str, default: t.Optional[t.Any] = ..., /
    ) -> t.Any: ...


@functools.cache
def lazy_load_getattr_static() -> _GetAttr:
    """Lazy loader for :func:`inspect.getattr_static()`.

    This delays loading the `inspect` module until the first
    instance/subclass check against an `AttrCheckProtocol`, since the
    module is rather heavy.

    This has been copied from the Python 3.12+ `typing` module.
    """
    from inspect import getattr_static

    return getattr_static


class AttrCheckProtocol(t.Protocol, metaclass=AttrCheckProtocolMeta):
    """Base class for protocols that check attributes and class methods.

    Subclassing `AttrCheckProtocol` is largely the same as subclassing
    `Protocol` directly. However, when creating
    a `runtime_checkable` protocol using `AttrCheckProtocol`, it
    will work with :func:`issubclass()` *even if* your protocol defines
    attributes, properties or class methods.

    Note:
        Due to limitations in type checkers like MyPy, it might be
        necessary that your protocols subclass both `AttrCheckProtocol`
        and `Protocol` directly in order to be recognized as protocols.
        This has no impact on runtime behavior.

    Protocol members are collected in the **same way as in Python
    3.12+**, meaning: at class creation time. You may monkey-patch
    a protocol with additional methods or attributes after class
    creation, but those members will not be considered in
    :func:`isinstance()` and :func:`issubclass()` checks.

    The :func:`isinstance()` check mostly aligns with Python 3.12+,
    meaning: it is based on :func:`~inspect.getattr_static()` and might
    not find dynamically generated attributes. However, for each
    protocol member that is a `classmethod`, it additionally tests that
    the class of the tested instance provides a `classmethod` of that
    name as well. Properties and normal functions are rejected.

    Checks with :func:`issubclass()` work even if the protocol defines
    non-method members. Protocol class methods are tested similarly to
    :func:`isinstance()` checks, except on the subclass directly (and
    not on its metaclass).

    Checks with :func:`issubclass()` for regular protocol methods are
    stricter than for `Protocol`. Not only must the subclass have an
    attribute of the same name, it must also be callable (like for
    :func:`isinstance()` checks).

    Just like with `Protocol`, checks with :func:`issubclass()` may
    also be satisfied if the tested subclass is itself a protocol and
    contains an *annotation* with the same name as a protocol attribute.
    Class methods are treated like other attributes here.

    Examples:

        >>> from typing import Any, runtime_checkable
        ...
        >>> @runtime_checkable
        ... class MyProtocol(AttrCheckProtocol):
        ...     def meth(self): pass
        ...     @classmethod
        ...     def c_meth(cls): pass
        ...     attr: dict[str, Any]
        ...

    Other objects must at least contain the specified attributes to
    implement the protocol:

        >>> class Good:
        ...     def meth(self): pass
        ...     @classmethod
        ...     def c_meth(cls): pass
        ...     attr = {}
        ...
        >>> isinstance(Good(), MyProtocol)
        True
        >>> issubclass(Good, MyProtocol)
        True
        >>> isinstance(1, MyProtocol)
        False
        >>> issubclass(int, MyProtocol)
        False

    A regular method in place of a class method is rejected:

        >>> class Bad:
        ...     def meth(self): pass
        ...     def c_meth(self): pass
        ...     attr = {}
        ...
        >>> isinstance(Bad(), MyProtocol)
        False
        >>> issubclass(Bad, MyProtocol)
        False

    Attributes:
        _is_protocol (bool): Flag that indicates whether a subclass of
            `Protocol` is itself a protocol or a concrete class.
            `Protocol` determines its value in
            `~AttrCheckProtocol.__init_subclass__()`;
            `AttrCheckProtocolMeta` pre-empts this in
            `~AttrCheckProtocolMeta.__new__()`.

        _is_runtime_protocol (bool): Flag that indicates whether
            a protocol can be used in :func:`isinstance()` and
            :func:`issubclass()` checks. This is set by
            `runtime_checkable`.

        __protocol_attrs__ (set[str]): Cached collection of all protocol
            members, no matter whether they're a nested :term:`variable
            annotation`, a :term:`method`, a `classmethod`, a `property`
            or a regular :term:`attribute`. This is set by
            `AttrCheckProtocolMeta.__init__()` if the class is
            a protocol. It doesn't exist on concrete classes (but may
            still be found via the :term:`method resolution order`).

            Both the standard library and this module have a list of
            `_SPECIAL_NAMES` that never appear here.

        __non_callable_proto_members__ (set[str]): Cached collection of
            all protocol members that are not methods, class methods or
            static methods, i.e. properties, attributes and variable
            annotations. This is set by `runtime_checkable` [#rtp]_, so
            it doesn't exist on non-runtime protocols. It is always
            a subset of `__protocol_attrs__`.

            It is also set by `non_callable_proto_members()` if it
            doesn't exist yet. This may be the case on older Python
            versions that don't know this attribute yet.

        __proto_classmethods__ (set[str]): Cached collection of all
            protocol members that are class methods. This is created
            lazily the first time `proto_classmethods()` is called.
            Thus, you always have to assume that it doesn't exist yet.

            This is always a subset of `__protocol_attrs__`. It is
            a strict invention of this module and does not interact with
            `Protocol` in any way.

    .. method:: __init__(*args, **kwargs)

        This method is provided by `Protocol` and is not our implementation.

        All subclasses that are protocols themselves have their
        :meth:`~object.__init__()` initializer replaced by a special
        dummy that prevents them from being instantiated. This
        replacement occurs inside `__init_subclass__()`. If this dummy
        gets called from a concrete class (e.g. because that concrete
        class doesn't define an initializer), it searches the MRO for
        any initializer other than itself and replaces itself with it.

        One quirk of the dummy is that if it gets called via
        :class:`super() <super>` from a concrete class that already has
        a custom initializer, it will return immediately and call
        ``super().__init__()`` itself. In some cases of multiple
        inheritance, this may break the initialization chain and leave
        an object partially uninitialized. If you run into this issue,
        we propose `filing an issue
        <https://github.com/python/cpython/issues/>`_ with the CPython
        project.

    .. method:: __init_subclass__(*args, **kwargs)
        :classmethod:

        This method is provided by `Protocol` and is not our implementation.

        The :meth:`~object.__init_subclass__()` class method is called
        automatically by :class:`type.__new__() <type>` during class
        creation. (See :ref:`std:Metaclasses` for more information.) For
        protocols, it updates three attributes:

        - `_is_protocol` is set to True if the subclass inherits from
          `Protocol` *directly*, and to False otherwise. If
          `_is_protocol` is already True, it is not modified.
        - The protocol `__subclasshook__` is injected if the subclass
          doesn't have a custom :meth:`~abc.ABCMeta.__subclasshook__()`.
        - The protocol `__init__` is injected if the subclass is
          a protocol and doesn't have a custom
          :meth:`~object.__init__()`.

        The first two attributes are pre-empted by
        `AttrCheckProtocolMeta.__new__()` with our own checks. By
        setting these attributes before `Protocol` can, we can override
        them with our own logic.
    """

    __slots__ = ()

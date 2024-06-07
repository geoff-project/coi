# SPDX-FileCopyrightText: 2020-2024 CERN
# SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = missing-class-docstring
# pylint: disable = missing-function-docstring

"""Add custom directives for this package.

These custom directives are:

- ``entrypoint`` with the role ``:std:ep:``;
- ``rendermode`` with the role ``:std:rmode:``;
- ``metadatakey`` with the role ``:std:mdkey:``.
"""

from __future__ import annotations

import typing as t
from logging import getLogger

import sphinx
from docutils.nodes import Text
from docutils.parsers.rst import directives
from sphinx.addnodes import (
    desc_addname,
    desc_annotation,
    desc_name,
    desc_returns,
    desc_sig_punctuation,
    desc_sig_space,
)
from sphinx.domains import ObjType
from sphinx.domains.python._annotations import _parse_annotation
from sphinx.domains.std import GenericObject
from sphinx.errors import ExtensionError
from sphinx.roles import XRefRole

if t.TYPE_CHECKING:
    from docutils.nodes import TextElement
    from docutils.parsers.rst import Directive
    from sphinx.addnodes import desc_signature
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec

LOG = getLogger(__name__)


def add_object_type(
    app: Sphinx,
    *,
    directivename: str,
    rolename: str,
    objname: str,
    directive: type[Directive],
    ref_nodeclass: type[TextElement] | None = None,
    override: bool = False,
) -> None:
    LOG.debug(
        "[app] adding object type: %r",
        (directivename, rolename, ref_nodeclass, objname),
    )
    app.add_directive_to_domain("std", directivename, directive)
    app.add_role_to_domain("std", rolename, XRefRole(innernodeclass=ref_nodeclass))
    object_types = app.registry.domain_object_types.setdefault("std", {})
    if directivename in object_types and not override:
        raise ExtensionError(f"The {directivename!r} object_type is already registered")
    object_types[directivename] = ObjType(objname or directivename, rolename)


class GenericDictKey(GenericObject):
    option_spec: t.ClassVar[OptionSpec] = GenericObject.option_spec.copy()
    option_spec.update(
        {
            "type": directives.unchanged,
            "value": directives.unchanged,
        }
    )

    dict_name: str = "dict"

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        if not sig[0] == sig[-1] == '"':
            raise ValueError
        signode.clear()
        signode += desc_addname("", self.dict_name, desc_sig_punctuation("", "["))
        signode += desc_name(sig, sig)
        signode += desc_addname("", "", desc_sig_punctuation("", "]"))
        signode["_toc_name"] = sig
        refname = sphinx.util.ws_re.sub(" ", sig)
        if typ := self.options.get("type"):
            annotations = _parse_annotation(typ, self.env)
            signode += desc_annotation(
                typ, "", desc_sig_punctuation("", ":"), desc_sig_space(), *annotations
            )
        if value := self.options.get("value"):
            signode += desc_annotation(
                value,
                "",
                desc_sig_space(),
                desc_sig_punctuation("", "="),
                desc_sig_space(),
                Text(value),
            )
        return refname

    def _toc_entry_name(self, sig_node: desc_signature) -> str:
        return sig_node.get("_toc_name", "")

    def _object_hierarchy_parts(self, sig_node: desc_signature) -> tuple[str, ...]:
        if name := sig_node.get("_toc_name"):
            return (name,)
        return ()


class MetadataKey(GenericDictKey):
    dict_name = "metadata"
    indextemplate = "metadata key; %s"


class InfoDictKey(GenericDictKey):
    dict_name = "info"
    indextemplate = "info dict key; %s"


class RenderMode(GenericObject):
    option_spec: t.ClassVar[OptionSpec] = GenericObject.option_spec.copy()
    option_spec.update({"rtype": directives.unchanged})

    indextemplate = "render mode; %s"

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        signode.clear()
        signode += desc_annotation("", "render mode", desc_sig_space())
        signode += desc_name(sig, sig)
        signode["_toc_name"] = sig
        refname = sphinx.util.ws_re.sub(" ", sig)
        if rtype := self.options.get("rtype"):
            annotations = _parse_annotation(rtype, self.env)
            signode += desc_returns(rtype, "", *annotations)
        return refname

    def _toc_entry_name(self, sig_node: desc_signature) -> str:
        return sig_node.get("_toc_name", "")

    def _object_hierarchy_parts(self, sig_node: desc_signature) -> tuple[str, ...]:
        if name := sig_node.get("_toc_name"):
            return (name,)
        return ()


class EntryPointGroup(GenericObject):
    option_spec: t.ClassVar[OptionSpec] = GenericObject.option_spec.copy()
    option_spec.update({"rtype": directives.unchanged})

    indextemplate = "entry point; %s"

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        signode.clear()
        signode += desc_annotation("", "entry point group", desc_sig_space())
        signode += desc_name(sig, sig)
        signode["_toc_name"] = sig
        refname = sphinx.util.ws_re.sub(" ", sig)
        if rtype := self.options.get("rtype"):
            annotations = _parse_annotation(rtype, self.env)
            signode += desc_returns(rtype, "", *annotations)
        return refname

    def _toc_entry_name(self, sig_node: desc_signature) -> str:
        return sig_node.get("_toc_name", "")

    def _object_hierarchy_parts(self, sig_node: desc_signature) -> tuple[str, ...]:
        if name := sig_node.get("_toc_name"):
            return (name,)
        return ()


class InstallExtra(GenericObject):
    indextemplate = "install extra; %s"

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        signode.clear()
        signode += desc_name(sig, sig)
        signode["_toc_name"] = sig
        return sphinx.util.ws_re.sub(" ", sig)

    def _toc_entry_name(self, sig_node: desc_signature) -> str:
        return sig_node.get("_toc_name", "")

    def _object_hierarchy_parts(self, sig_node: desc_signature) -> tuple[str, ...]:
        if name := sig_node.get("_toc_name"):
            return (name,)
        return ()


def setup(app: Sphinx) -> ExtensionMetadata:
    add_object_type(
        app,
        directivename="metadatakey",
        rolename="mdkey",
        objname="metadata key",
        directive=MetadataKey,
    )
    add_object_type(
        app,
        directivename="infodictkey",
        rolename="idkey",
        objname="info dict key",
        directive=InfoDictKey,
    )
    add_object_type(
        app,
        directivename="rendermode",
        rolename="rmode",
        objname="render mode",
        directive=RenderMode,
    )
    add_object_type(
        app,
        directivename="entrypoint",
        rolename="ep",
        objname="entry point",
        directive=EntryPointGroup,
    )
    add_object_type(
        app,
        directivename="extra",
        rolename="extra",
        objname="install extra",
        directive=InstallExtra,
    )
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

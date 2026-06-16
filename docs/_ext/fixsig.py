# SPDX-FileCopyrightText: 2020-2026 CERN
# SPDX-FileCopyrightText: 2023-2026 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""A number of small fixes to autodoc-generated signatures."""

from __future__ import annotations

import enum
import re
import typing as t

from sphinx.util.logging import getLogger

if t.TYPE_CHECKING:
    from sphinx.application import Config, Sphinx
    from sphinx.util.typing import ExtensionMetadata


LOG = getLogger(__name__)


def hide_enum_init_args(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str,
    return_annotation: str | None,
) -> tuple[str, str | None] | None:
    """Hide all enum args except the first one."""
    if what == "class" and isinstance(obj, type) and issubclass(obj, enum.Enum):
        oldsig = signature
        # Extract all args and only keep the first.
        arg = signature.strip("()").split(", ", 1)[0].strip("*")
        signature = f"({arg!s}: str)"
        LOG.info(
            "hide enum args: %s -> %s",
            oldsig,
            signature,
            type="fixsig",
            subtype="hide_enum_init_args",
        )
        return signature, return_annotation
    return None


def hide_exception_init_args(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str,
    return_annotation: str | None,
) -> tuple[str, str | None] | None:
    """Hide all exception args."""
    if (
        what == "exception"
        and isinstance(obj, type)
        and issubclass(obj, Exception)
        and signature
    ):
        LOG.info(
            "hide exc args: %s%s",
            name,
            signature,
            type="fixsig",
            subtype="hide_exception_init_args",
        )
        return "", return_annotation
    return None


def hide_mcs_init_args(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str,
    return_annotation: str,
) -> tuple[str, str | None] | None:
    """Hide all metaclass args."""
    if what == "class" and isinstance(obj, type) and issubclass(obj, type):
        LOG.info(
            "hide mcs args: %s%s",
            name,
            signature,
            type="fixsig",
            subtype="hide_mcs_init_args",
        )
        return "", return_annotation
    return None


def _type_alias_forward_ref_repl(match: re.Match[str]) -> str:
    LOG.info(
        "hide TypeAliasForwardRef: %s -> %s",
        match.group(0),
        match.group(1),
        type="fixsig",
        subtype="hide_type_alias_forward_ref",
    )
    return match.group(1)


def _type_alias_forward_ref_apply(sig: str, name: str) -> str:
    LOG.info(
        "hide TypeAliasForwardRef: %s",
        name,
        type="fixsig",
        subtype="hide_type_alias_forward_ref",
    )
    return re.sub(
        r"\bTypeAliasForwardRef\('(~?[\w\.]+)'\)", _type_alias_forward_ref_repl, sig
    )


def hide_type_alias_forward_ref(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str | None, str | None] | None:
    """Hide the spurious type `TypeAliasForwardRef` in return annotations."""
    modified = False
    if signature is not None and "TypeAliasForwardRef" in signature:
        signature = _type_alias_forward_ref_apply(signature, name)
        modified = True
    if return_annotation is not None and "TypeAliasForwardRef" in return_annotation:
        return_annotation = _type_alias_forward_ref_apply(return_annotation, name)
        modified = True
    if modified:
        return signature, return_annotation
    return None


def hide_sentinel_values(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str | None,
    return_annotation: str | None,
) -> tuple[str, str | None] | None:
    """Hide default values that are surrounded by angle brackets.

    This circumvents https://github.com/sphinx-doc/sphinx/issues/12695.
    """
    if not signature:
        return None
    signature = re.sub(r"<[\w\.]+>", "...", signature)
    return signature, return_annotation


def install_handlers(app: Sphinx, config: Config) -> None:
    """Read config and install fixers."""
    if config.fixsig_hide_type_alias_forward_ref:
        app.connect("autodoc-process-signature", hide_type_alias_forward_ref)
    if config.fixsig_hide_enum_init_args:
        app.connect("autodoc-process-signature", hide_enum_init_args)
    if config.fixsig_hide_exception_init_args:
        app.connect("autodoc-process-signature", hide_exception_init_args)
    if config.fixsig_hide_mcs_init_args:
        app.connect("autodoc-process-signature", hide_mcs_init_args)
    if config.fixsig_hide_sentinel_values:
        app.connect("autodoc-process-signature", hide_sentinel_values)


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up hooks into Sphinx."""
    app.add_config_value("fixsig_hide_type_alias_forward_ref", False, "env", bool)
    app.add_config_value("fixsig_hide_enum_init_args", False, "env", bool)
    app.add_config_value("fixsig_hide_exception_init_args", False, "env", bool)
    app.add_config_value("fixsig_hide_mcs_init_args", False, "env", bool)
    app.add_config_value("fixsig_hide_sentinel_values", False, "env", bool)
    app.connect("config-inited", install_handlers)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
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
        arg = signature.strip("()").split(", ", 1)[0]
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


def hide_type_alias_forward_ref(
    app: Sphinx,
    what: str,
    name: str,
    obj: object,
    options: dict[str, bool],
    signature: str,
    return_annotation: str | None,
) -> tuple[str, str | None] | None:
    """Hide the spurious type `TypeAliasForwardRef` in return annotations."""
    if return_annotation is not None and "TypeAliasForwardRef" in return_annotation:
        LOG.info(
            "hide TypeAliasForwardRef: %s",
            name,
            type="fixsig",
            subtype="hide_type_alias_forward_ref",
        )

        def repl(match: re.Match[str]) -> str:
            LOG.info(
                "hide TypeAliasForwardRef: %s -> %s",
                match.group(0),
                match.group(1),
                type="fixsig",
                subtype="hide_type_alias_forward_ref",
            )
            return match.group(1)

        return_annotation = re.sub(
            r"\bTypeAliasForwardRef\('(~?[\w\.]+)'\)", repl, return_annotation
        )
        return signature, return_annotation
    return None


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


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up hooks into Sphinx."""
    app.add_config_value("fixsig_hide_type_alias_forward_ref", False, "env", bool)
    app.add_config_value("fixsig_hide_enum_init_args", False, "env", bool)
    app.add_config_value("fixsig_hide_exception_init_args", False, "env", bool)
    app.add_config_value("fixsig_hide_mcs_init_args", False, "env", bool)
    app.connect("config-inited", install_handlers)
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

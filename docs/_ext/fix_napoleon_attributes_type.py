# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

"""Fix the way Napoleon documents attributes.

This is a workaround for
<https://github.com/sphinx-doc/sphinx/issues/7582>. It works by
monkey-patching the method ``_parse_attributes_section()`` of
`napoleon.GoogleDocstring`. The patched method does *not* support the
config option ``napoleon_use_ivar``. If this option is set to True, the
method raises a `ValueError`.
"""

from __future__ import annotations

import typing as t

from sphinx.ext import napoleon

if t.TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


def _parse_attributes_section(
    self: napoleon.GoogleDocstring, section: str
) -> list[str]:
    """Work around for https://github.com/sphinx-doc/sphinx/issues/7582."""
    if self._config.napoleon_use_ivar:
        raise ValueError(
            "Monkeypatched `_parse_attributes_section()` does not "
            "support 'napoleon_use_ivar'"
        )
    lines = []
    for _name, _type, _desc in self._consume_fields():
        if not _type:
            _type = self._lookup_annotation(_name)
        lines.append(".. attribute:: " + _name)
        if _type:
            lines.extend(self._indent([f":type: {_type!s}"], 3))
        if self._opt and ("no-index" in self._opt or "noindex" in self._opt):
            lines.append("   :no-index:")
        lines.append("")

        fields = self._format_field("", "", _desc)
        lines.extend(self._indent(fields, 3))
        lines.append("")
    return lines


def setup(app: Sphinx) -> ExtensionMetadata:
    """Set up hooks into Sphinx."""
    napoleon.GoogleDocstring._parse_attributes_section = _parse_attributes_section  # type: ignore[method-assign]
    return {
        "version": "1.0",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

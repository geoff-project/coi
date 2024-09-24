#!/usr/bin/env python

# SPDX-FileCopyrightText: 2020 - 2024 CERN
# SPDX-FileCopyrightText: 2023 - 2024 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# pylint: disable = unused-import

"""Run the environment checkers over the example environments."""

from typing import Any

from cernml import coi
from cernml.coi import cancellation

for plugin in ["configurable", "parabola"]:
    __import__(plugin)

if not coi.registry.all():
    raise AssertionError("no environments registered")

for spec in coi.registry.all():
    print("Checking", spec.id, "…")
    kwargs: dict[str, Any] = {}
    assert coi.is_problem_class(spec.entry_point), spec
    if spec.entry_point.metadata.get("cern.cancellable", False):
        kwargs["cancellation_token"] = cancellation.Token()
    env = coi.make(spec.id, **kwargs)
    coi.check(env, headless=True, warn=True)

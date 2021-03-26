#!/usr/bin/env python
"""Run the environment checkers over the example environments."""

# pylint: disable = unused-import

import configurable
import parabola

from cernml import coi
from cernml.coi.unstable import cancellation

if not coi.registry.all():
    raise AssertionError("no environments registered")

for spec in coi.registry.all():
    print("Checking", spec.id, "…")
    kwargs = {}
    if spec.entry_point.metadata.get("cern.cancellable", False):
        kwargs["cancellation_token"] = cancellation.Token()
    env = coi.make(spec.id, **kwargs)
    coi.check(env, headless=True, warn=True)

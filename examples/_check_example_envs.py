#!/usr/bin/env python
"""Run the environment checkers over the example environments."""

# pylint: disable = unused-import

from cernml import coi
import parabola
import configurable


if not coi.registry.all():
    raise AssertionError("no environments registered")

for spec in coi.registry.all():
    print("Checking", spec.id, "…")
    env = coi.make(spec.id)
    coi.check(env, headless=True, warn=True)

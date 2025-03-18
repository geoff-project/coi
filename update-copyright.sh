#!/bin/bash

# SPDX-FileCopyrightText: 2024 - 2025 CERN
# SPDX-FileCopyrightText: 2024 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# Use https://github.com/fsfe/reuse-tool to add the current year to all
# copyright headers.

args=(
    --merge-copyrights
    --fallback-dot-license
    --license="GPL-3.0-or-later OR EUPL-1.2+"
    --copyright="CERN"
    --copyright="GSI Helmholtzzentrum für Schwerionenforschung"
    --year="$(date +%Y)"
    --template=geoff
)

reuse annotate "${args[@]}" --recursive .

# Some files are also under copyright via other, active projects. Update their
# years as well.
farama_files=(
    src/cernml/coi/_goalenv.py
    src/cernml/coi/registration/__init__.py
    src/cernml/coi/registration/_base.py
    src/cernml/coi/registration/_globals.py
    src/cernml/coi/registration/_make.py
    src/cernml/coi/registration/_registry.py
    src/cernml/coi/registration/_spec.py
    src/cernml/coi/registration/_specdict.py
    src/cernml/coi/registration/errors.py
)
reuse annotate "${args[@]}" --copyright="Farama Foundation" "${farama_files[@]}"

psf_files=(
    docs/_static/pydoctheme.css
    docs/_templates/layout.html
)
reuse annotate "${args[@]}" --copyright="Python Software Foundation" "${psf_files[@]}"

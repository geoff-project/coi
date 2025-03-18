#!/usr/bin/env sh

# SPDX-FileCopyrightText: 2020 - 2025 CERN
# SPDX-FileCopyrightText: 2023 - 2025 GSI Helmholtzzentrum für Schwerionenforschung
# SPDX-FileNotice: All rights not expressly granted are reserved.
#
# SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

# If the user hasn't already set up a proxy ...
if [ -z "$HTTPS_PROXY" ]; then
    acc_py_addr="https://acc-py.web.cern.ch/"
    proxy_addr="socks5://localhost:3694"

    # Check if we can reach Acc-Py docs server.
    # If we can't normally, but we can with a proxy, use that proxy.
    # Otherwise, proceed, but put out a warning.
    if ! curl -sI "$acc_py_addr" >/dev/null; then
        if ! curl -sIx "$proxy_addr" "$acc_py_addr" >/dev/null; then
            echo >&2 'warning: cannot reach acc-py docs server'
            echo >&2 'hint: run `ssh -ND localhost:3694 lxtunnel.cern.ch` ' \
                'in the background'
        else
            export HTTPS_PROXY="$proxy_addr"
        fi
    fi
fi

sphinx-build docs/ docs/html "$@"

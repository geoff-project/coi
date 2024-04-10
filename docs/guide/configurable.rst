..
    SPDX-FileCopyrightText: 2020-2024 CERN
    SPDX-FileCopyrightText: 2023-2024 GSI Helmholtzzentrum für Schwerionenforschung
    SPDX-FileNotice: All rights not expressly granted are reserved.

    SPDX-License-Identifier: GPL-3.0-or-later OR EUPL-1.2+

Making an Optimization Configurable via GUI
===========================================

.. currentmodule:: cernml.coi

This section introduces a few useful, but less common interfaces defined by Gym
and the COI.

.. digraph:: control_flow
    :caption: Fig. 1: Sequence diagram of the Configurable API

    newrank = true;
    node[
        shape=box,
        fontname="Open Sans",
        style="rounded, filled",
        fillcolor="white",
    ];

    subgraph cluster_user {
        label = "User";
        configure[label="Configure problem"];
        modify[label="Modify values"];
        submit[label="Submit new values"];
        end[label="Present success/failure"];
    }

    subgraph cluster_host {
        label = "Host";
        get_config[label="problem.get_config()"];
        get_field_values[label="config.get_field_values()"];
        validate[label="config.validate_all(values)"];
        apply_config[label="problem.apply_config(validated)"];
        return_host[label="return", shape=plaintext];
    }

    subgraph cluster_plugin {
        label = "Plugin";
        make_config[label="Config().add(…).add(…)"];
        return_config[label="return config", shape=plaintext];
        use_config[label="self.field = validated.field"];
        return_none[label="return", shape=plaintext];
    }

    { rank=same; configure; get_config; make_config; }
    { rank=same; modify; get_field_values; return_config; }
    { rank=same; submit; validate; }
    { rank=same; apply_config; use_config; }
    { rank=same; end; return_host; return_none; }

    configure -> get_config -> make_config;
    make_config -> return_config;
    return_config -> get_field_values -> modify [style=dashed];
    modify -> submit;
    submit -> validate;
    validate -> apply_config;
    apply_config -> use_config;
    use_config -> return_none;
    return_none -> return_host -> end [style=dashed];

The *Configurable* API provides a uniform way for problem authors to declare
parameters of their class that can be modified before (but not during) an
optimization run. It also allows specifying certain variants for each
parameter. Host applications can use this interface to present a configuration
dialog to the user.

Usage examples are shown in the API reference for `Configurable`.

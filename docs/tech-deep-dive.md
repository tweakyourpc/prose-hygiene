# Technical Deep Dive

## Overview

`prose-hygiene` is a deterministic cleanup layer for AI-assisted documentation workflows. It is intentionally narrow: instead of trying to rewrite prose broadly, it focuses on a small set of high-signal artifacts that can be handled with explainable heuristics.

## Core architecture

The implementation is split into three primary layers:
- `style.py` applies line-level punctuation heuristics
- `engine.py` handles files, directories, zip archives, ignore markers, and reporting
- `cli.py` exposes the engine as a predictable command-line interface

That separation keeps the highest-risk logic in one place while allowing multiple delivery surfaces.

## Rewrite model

The rewrite engine is not doing naive global replacement. It tries to classify common em dash uses into a few narrow cases:
- heading-style label and detail pairs
- list-item descriptors
- parenthetical insertions
- serial sequences
- discourse transitions that should become commas

When a line falls outside those cases, the behavior stays conservative and predictable.

## Artifact handling

The engine supports:
- single files
- directory trees
- zip archives

Each run produces a structured report that includes:
- file-level status
- total matches
- rewrite strategies used
- any error states

## Hook design

The Git hook model uses a dispatcher script plus ordered executables in `pre-commit.d/`. That allows multiple hygiene layers to coexist:
- an auto-fix pass for deterministic cleanup
- an advisory-only pass for suspicious AI-style phrases

The auto-fix hook now skips files that have unstaged working-tree changes so it does not overwrite local edits during partial staging workflows.

## Why this approach is interesting

The interesting claim is not that em dashes are special. It is that AI-generated documentation drift often shows up in repetitive, narrow patterns that are a good fit for deterministic local cleanup.

That makes the project useful both as a tool and as a design argument for tighter integration between coding agents and repository-native hygiene systems.

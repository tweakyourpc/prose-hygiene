# Technical Deep Dive

## Overview

`prose-hygiene` is a deterministic cleanup layer for AI-assisted documentation workflows. It is intentionally narrow: instead of trying to rewrite prose broadly, it focuses on a small set of high-signal punctuation artifacts that can be handled with explainable heuristics.

## Core architecture

The implementation is split into three primary layers:
- `style.py` applies line-level punctuation heuristics
- `engine.py` handles files, directories, zip archives, ignore markers, and reporting
- `cli.py` exposes the engine as a predictable command-line interface

That separation keeps the highest-risk logic in one place while allowing multiple delivery surfaces.

## Rewrite model

The rewrite engine is not doing naive global replacement. It first normalizes a small family of punctuation forms into a predictable internal model, then classifies common usages into narrow cases.

Today that includes:
- em dash separator usage
- en dash separator usage where it behaves like prose punctuation
- en dash numeric ranges that should become ASCII hyphens
- space-flanked `--`
- optional heading-style comma normalization

The separator-classification layer tries to map lines into a few explainable cases:
- heading-style label and detail pairs
- list-item descriptors
- parenthetical insertions
- serial sequences
- discourse transitions that should become commas

When a line falls outside those cases, the behavior stays conservative and predictable.

## Structured-region safety

The engine avoids rewriting regions that are likely to be structured syntax rather than prose:
- fenced code blocks
- inline backticks
- YAML frontmatter
- HTML comments

That boundary matters because a hygiene tool should improve prose without damaging examples, metadata, or markup.

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

The important claim is not that any one punctuation mark is special. It is that AI-generated documentation drift often shows up in repetitive, narrow patterns that are a good fit for deterministic local cleanup.

That makes the project useful both as a tool and as a design argument for tighter integration between coding agents and repository-native hygiene systems.

# Known Limitations

- Unmatched multi-em-dash constructions still fall back to comma replacement.
- The autofix hook skips files with unstaged working-tree changes to avoid overwriting local edits. Those files must be staged cleanly and committed on a later pass.
- The web frontend is experimental and not yet as hardened as the CLI/hook workflow.

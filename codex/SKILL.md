---
name: scrub
description: Run the installed prose-hygiene CLI on a file or directory to remove U+2014 characters from documentation and other text artifacts. Use when the user asks to scrub a file, folder, docs tree, or repo content, or asks to remove em dashes before commit.
---

# Scrub

Use this skill when the user explicitly asks to "scrub" a file or directory, or asks to run `prose-hygiene`.

## Workflow

1. Prefer the installed CLI:

   ```bash
   prose-hygiene <input_path> <output_path> --json
   ```

2. For a single file that should be updated in place, write to a temporary output path first, inspect the JSON report, then replace the original only if the command succeeds.

3. For a directory, write to a separate output directory first. Replace or sync back only after the scrub completes successfully.

4. Report the JSON summary fields that matter:
   - `summary.fixed`
   - `summary.matches`
   - `strategies`

5. The scrubber scans these extensions:
   - `.md`
   - `.mdx`
   - `.txt`
   - `.rst`
   - `.yaml`
   - `.yml`
   - `.toml`
   - `.json`

6. If the user is asking about commits or repo-wide enforcement, note that a global Git `pre-commit` hook may already be installed and can auto-fix staged files before commit.

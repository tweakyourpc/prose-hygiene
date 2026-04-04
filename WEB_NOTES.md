# Web Notes

> **EXPERIMENTAL**: `web.py` is a local/demo interface and should not be treated as the primary release surface.

The web module provides a self-contained local frontend for uploading a file, folder, or zip archive and downloading a cleaned result. It is useful for demos and local workflows, but it deliberately trails the CLI and hook flow in support level.

Current hardening work includes:
- a required `/whoami` endpoint for service identification
- cleanup of temporary storage on shutdown
- rejection of unsafe folder-upload traversal paths

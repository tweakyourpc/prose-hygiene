# Security Policy

## Scope

`prose-hygiene` is a local documentation-cleanup tool. The primary supported surfaces are:
- the CLI
- the Git hook workflow

The web demo is intentionally labeled experimental and should not be treated as a hardened multi-user service.

## Reporting

If you find a security issue, open a private report through the repository hosting platform if available. If private reporting is not available yet, avoid posting exploit details in a public issue until a fix is ready.

## Expected threat model

The project is designed for local, trusted workflows:
- it runs on local files and local Git state
- it does not call external models or external APIs
- it should not require network access for normal operation

## Hardening notes

- folder uploads in the web demo reject traversal-style relative paths
- the `/whoami` endpoint exists for service identification
- the auto-fix hook skips files with unstaged working-tree changes to avoid destructive overwrites

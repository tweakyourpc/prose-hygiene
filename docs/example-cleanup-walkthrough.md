# Example Cleanup Walkthrough

## Input

```md
# Responses Sheet — Column Reference

The rollout is ready — but only after restart.
- Inventory tab — paste from SolarWinds
```

## JSON report

```json
{
  "kind": "file",
  "summary": {
    "files": 1,
    "scanned": 1,
    "fixed": 1,
    "ignored": 0,
    "clean": 0,
    "copied": 0,
    "errors": 0,
    "matches": 3
  },
  "strategies": {
    "colon": 2,
    "comma": 1
  },
  "files": [
    {
      "relative_path": "README.md",
      "status": "fixed",
      "scanned": true,
      "count": 3,
      "strategies": {
        "colon": 2,
        "comma": 1
      }
    }
  ]
}
```

## Output

```md
# Responses Sheet: Column Reference

The rollout is ready, but only after restart.
- Inventory tab: paste from SolarWinds
```

## Why this example matters

This is the shortest way to show the full loop:
- a small documentation artifact with recognizable AI-style punctuation drift
- a deterministic report describing what changed
- a cleaned result that is ready to stage or review

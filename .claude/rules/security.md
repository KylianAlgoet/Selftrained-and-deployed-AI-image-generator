# Security rules

## Untrusted input

Treat all uploads as untrusted:
- Extension and MIME checks against an allowlist (PNG/JPG/WEBP)
- Decode validation (actually open the image; reject on failure)
- Size limits (dimensions and bytes)
- Random internal filenames; never reuse user-supplied names
- Path-traversal prevention; never join user input into filesystem paths
- Temporary-file cleanup after processing
- Restricted CORS to the known frontend origin
- Safe error messages; never leak local paths or stack traces
- Timeouts on generation requests

## Never commit

`.env` and real secrets, tokens, passwords, keys, personal images, temporary uploads, private datasets, model caches, pretrained weights, unapproved large checkpoints, `node_modules`, virtual environments, build caches, or sensitive logs. `.env.example` contains placeholders only.

Before each commit: scan the staged diff for secrets and confirm no large binaries are staged (see git-commit-protocol.md).

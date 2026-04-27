# /secrets — production secret files

This directory holds file-backed Docker secrets that
`docker-compose.caddy.yml` mounts into containers as
`/run/secrets/<name>`.

**Never commit anything here except this README.**
The contents of `*.txt` files are gitignored (see top-level `.gitignore`).

Provisioning, rotation, and incident response are documented in
`docs/runbook_secrets.md`.

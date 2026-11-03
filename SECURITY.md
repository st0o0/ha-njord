# Security Policy

## Supported versions

The latest release receives updates. Older versions are not maintained.

## Reporting a vulnerability

Please report security issues **privately** via GitHub's
[private vulnerability reporting](https://github.com/st0o0/ha-njord/security/advisories/new)
(Security > Advisories > *Report a vulnerability*). Do **not** open a public
issue for security problems.

You can expect an initial response within a few days. Once a fix is available it
is released and the advisory is published.

## Scope

ha-njord is a Home Assistant custom integration that connects to a njord instance
via gRPC. It handles no credentials beyond the njord host/port configuration.
Vulnerabilities in its Python dependencies should be reported upstream.

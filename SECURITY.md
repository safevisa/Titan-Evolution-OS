# Security policy

## Reporting a vulnerability

Please **do not** open a public GitHub issue for undisclosed security vulnerabilities.

- Email the maintainers with details and reproduction steps if a contact is listed in the repository or organization profile, **or**
- Use [GitHub private vulnerability reporting](https://github.com/safevisa/Titan-Evolution-OS/security/advisories/new) if enabled for this repository.

Include: affected version/commit, impact, and suggested fix if you have one.

## Scope

This project runs with secrets in environment variables and may call third-party LLM APIs. Operators are responsible for network isolation, TLS, key rotation, and access control on self-hosted deployments.

## Supported versions

Security fixes are applied on the default branch (`main`) unless a separate LTS branch is announced later.

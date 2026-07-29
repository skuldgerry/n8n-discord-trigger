# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-07-29

### Added

- Required `WEBHOOK_TOKEN` authentication through the standard
  `Authorization: Bearer` header.
- Required tokens in the `sk-` plus 64 lowercase hexadecimal character format.
- Configurable `WEBHOOK_TIMEOUT_SECONDS` setting.
- Regression tests for direct bot mentions, `@here`, `@everyone`, authentication,
  content cleanup, admin detection, and HTTP errors.
- A documented release and versioning strategy.

### Changed

- Trigger guild webhooks only when the bot user is explicitly mentioned.
- Preserve the existing direct-message trigger behavior.
- Deliver webhook requests asynchronously with a bounded timeout.
- Treat non-success HTTP responses as delivery failures.
- Resolve administrator status through Discord's guild permission calculation.
- Stop logging message contents and complete webhook payloads.
- Use least-privilege Discord invite permissions.
- Pin Python dependencies and run the container as a non-root user.

### Security

- Webhook authentication is now mandatory.
- Documented generation of a 256-bit `sk-` token using Python or OpenSSL.
- Removed the unnecessary privileged Guild Members intent.

### Breaking

- Deployments must set `WEBHOOK_TOKEN`.
- The n8n Webhook node must use Header Auth with an `Authorization` header
  whose value is `Bearer ` followed by the same token.

## [1.0.0] - 2025-07-27

### Added

- Initial Discord mention and direct-message webhook trigger.

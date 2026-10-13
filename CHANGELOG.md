# Changelog

All notable changes to this project are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2026-10-13

### Fixed

- Reject webhook redirects instead of following them and potentially reporting
  a login page as a successful delivery.
- Confirm delivery only for HTTP 2xx responses; report other statuses as failures.
- Add regression coverage for real HTTP redirects, unsuccessful responses,
  authenticated payload delivery, and bot delivery logging.

## [2.0.0] - 2026-07-29

### Added

- Required `WEBHOOK_TOKEN` authentication through the standard
  `Authorization: Bearer` header.
- Required tokens in the `sk-` plus 64 lowercase hexadecimal character format.
- Configurable `WEBHOOK_TIMEOUT_SECONDS` setting.
- Regression tests for direct bot mentions, `@here`, `@everyone`, authentication,
  content cleanup, admin detection, and HTTP errors.
- A documented release and versioning strategy.
- Persistent access to the public Discord invite URL through
  `/tmp/n8n-discord-trigger-invite-url.txt` inside the running container.

### Changed

- Trigger guild webhooks only when the bot user is explicitly mentioned.
- Preserve the existing direct-message trigger behavior.
- Deliver webhook requests asynchronously with a bounded timeout.
- Treat non-success HTTP responses as delivery failures.
- Resolve administrator status through Discord's guild permission calculation.
- Stop logging message contents and complete webhook payloads.
- Use least-privilege Discord invite permissions.
- Pin Python dependencies and run the container as a non-root user.
- Clarify that the n8n Header Auth value must include `Bearer ` and switch
  documented Python commands to `python3`.

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

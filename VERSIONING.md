# Versioning and releases

This project uses Semantic Versioning: `MAJOR.MINOR.PATCH`.

- **MAJOR**: incompatible deployment, environment-variable, payload, or trigger
  behavior changes.
- **MINOR**: backward-compatible functionality, optional configuration, or new
  payload fields.
- **PATCH**: backward-compatible bug fixes, dependency updates, documentation,
  and security fixes that do not require deployment changes.

Version `2.0.0` makes webhook authentication mandatory, so it is a major release.

## Release process

1. Add user-visible changes under `Unreleased` in `CHANGELOG.md`.
2. Choose the next version using the rules above.
3. Move the changes into a dated version section.
4. Update the runtime `VERSION` in `bot.py`.
5. Run the full test suite and build the container.
6. Tag the release as `vMAJOR.MINOR.PATCH`.
7. Publish an immutable Docker tag matching the version.

Docker releases should publish the exact version tag. Optional moving
`MAJOR.MINOR` and `MAJOR` tags may be updated only after the immutable image has
been validated. Avoid using `latest` in production deployments.

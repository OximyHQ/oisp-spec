# Changelog

All notable changes to the OISP specification will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-22

### Added

- Initial release of OISP specification
- Core event envelope schema with:
  - Event identification (id, type, timestamp)
  - Host context (hostname, os, device_id)
  - Actor context (user, uid, session)
  - Process context (pid, ppid, exe, cmdline)
  - Source provenance (collector, capture_method)
  - Confidence metadata (level, completeness, reasons)
- Common type schemas:
  - `host.schema.json` - Host/device context
  - `actor.schema.json` - User/identity context
  - `process.schema.json` - Process context
  - `confidence.schema.json` - Confidence metadata
- Event type schemas:
  - `process.schema.json` - Process lifecycle events
  - `network.schema.json` - Network activity events
  - `file.schema.json` - File operation events
  - `ai.schema.json` - AI request/response events
  - `agent.schema.json` - Agent/tool events
- Provider fingerprinting for:
  - OpenAI
  - Anthropic
  - Google (Gemini)
  - Azure OpenAI
  - AWS Bedrock
  - Cohere
  - Mistral
  - Ollama
- Protocol Buffer definitions
- Example events for common scenarios
- Initial documentation

[Unreleased]: https://github.com/oximyHQ/oisp-spec/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/oximyHQ/oisp-spec/releases/tag/v0.1.0


# Contributing to OISP Spec

Thank you for your interest in contributing to the OISP specification!

## Ways to Contribute

### Reporting Issues

- **Schema bugs**: If you find inconsistencies or errors in the JSON Schema or Protobuf definitions
- **Documentation**: Typos, unclear explanations, missing examples
- **Provider fingerprinting**: Missing providers, incorrect endpoint patterns
- **Feature requests**: New event types, additional fields, semantic conventions

### Submitting Changes

1. **Fork** the repository
2. **Create a branch** for your changes
3. **Make your changes** following the guidelines below
4. **Test** your changes (validate schemas, check examples)
5. **Submit a Pull Request**

## Guidelines

### Schema Changes

- All schema changes must be backwards-compatible within a minor version
- New required fields require a major version bump
- Include updated examples for any schema changes
- Update both JSON Schema and Protobuf definitions

### Semantic Conventions

- Follow OpenTelemetry naming conventions where applicable
- Use `snake_case` for attribute names
- Provide clear descriptions and examples
- Include the rationale for new conventions

### Provider Fingerprinting

- Document the source of endpoint information
- Include example requests/responses
- Test against actual API traffic when possible

### Code Style

- JSON: 2-space indentation, trailing newline
- YAML: 2-space indentation
- Markdown: 80-character line wrap for prose

## Development Setup

```bash
# Clone your fork
git clone https://github.com/oximyHQ/oisp-spec.git
cd oisp-spec

# Validate schemas (requires ajv-cli)
npm install -g ajv-cli
ajv validate -s schema/v0.1/envelope.schema.json -d examples/*.json
```

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

# Identity Catalog

This directory is the metadata registry layer for identity packs.

Purpose:
- Provide discoverable title/description metadata similar to skill discovery.
- Enable validation and lifecycle management of identities.
- Separate metadata registry concerns from runtime task state.

Core files:
- `identities.yaml`: registry of all identities in this project.
- `schema/identities.schema.json`: schema for registry validation.

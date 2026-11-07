# ADR-0003: Platform UI Direction

- Status: Accepted
- Date: 2026-11-07

## Context
The Platform UI should be visually distinct, minimal, functional on a phone, and suitable for a tile-based module dashboard. The user rejected a conventional SaaS/agent dashboard aesthetic and selected the Tile Terminal concept.

## Decision
Use a Tile Terminal visual direction:
- compact tile-oriented layout;
- terminal-inspired information density and clear boundaries;
- restrained dark palette with purposeful accent colors;
- monospaced typography where it helps convey status and metadata;
- interactive GUI controls rather than a fake command-line-only interface;
- minimal decoration and limited motion.

The Platform UI is planned as Svelte + Vite with custom CSS/design tokens, bundled into the Android Host. Modules retain full control over their own UI.

## Consequences
- Platform visual identity remains consistent across Hosts where practical.
- Platform UI framework is independent of the module framework.
- Responsive behavior and touch interaction are designed for Android phones.
- This fixes the visual direction, not every color, font, component, or animation detail.

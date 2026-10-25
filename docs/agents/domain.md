# Domain Docs

Layout: **single-context** (same as pp3).

## Before exploring, read these

- **`CONTEXT.md`** at the repo root (Thai glossary of game and development terms).
- **`docs/adr/`**: read ADRs that touch the area you're about to work in.
- Game concept and open questions: `docs/01_game_concept.md`.

If any of these files don't exist, proceed silently. The `/domain-modeling` skill creates them lazily when terms or decisions actually get resolved.

## Use the glossary's vocabulary

When your output names a domain concept (issue title, refactor proposal, test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

## Flag ADR conflicts

If a proposal contradicts an ADR, say so explicitly instead of silently overriding it.

# Vault conventions

This repo is an Obsidian vault synced via the Obsidian Git plugin.

- Link notes with wikilinks: `[[Note name]]`, not Markdown links. Note names are file names without `.md`.
- New notes without an obvious home go in `Inbox/`. Use `Templates/Note.md` as the shape: YAML frontmatter with `created` (YYYY-MM-DD) and `tags`.
- Daily notes live in `Daily/YYYY-MM-DD.md` and follow `Templates/Daily.md` with the date filled in (no `{{...}}` placeholders).
- Images and files go in `Attachments/`; embed with `![[file.png]]`.
- When renaming or moving a note, update every `[[link]]` that points to it.
- Don't edit `.obsidian/` unless asked. Never commit `workspace*.json`.

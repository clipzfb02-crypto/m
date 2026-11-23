# m

An Obsidian vault, synced through GitHub so Claude can read and edit it.

## Folders

| Folder | Use |
| --- | --- |
| `Inbox/` | Quick capture. New notes go here by default. |
| `Notes/` | Notes worth keeping. |
| `Projects/` | One note or subfolder per project. |
| `Daily/` | Daily notes, named `YYYY-MM-DD.md`. |
| `Templates/` | Templates for the core Templates plugin. |
| `Attachments/` | Images and files pasted into notes. |

## Connect Obsidian (desktop)

1. Clone this repo somewhere on your computer, e.g. `git clone https://github.com/clipzfb02-crypto/m.git`.
2. In Obsidian: **Open folder as vault** and pick the cloned folder.
3. Settings → Community plugins → turn off Restricted mode → Browse → install and enable **Git** (by Vinzent).
4. In the Git plugin settings, set **Auto commit-and-sync interval** (e.g. 10 minutes) and turn on **Pull on startup**.

Git must be installed and able to push to GitHub (sign in with Git Credential Manager, or use SSH).

## Connect Obsidian (mobile)

The Git plugin works on mobile but is slower and needs a GitHub personal access token. Alternatively, sync phone ↔ computer with Obsidian Sync or another file-sync app and let the desktop handle Git.

## Working with Claude

Claude works on this repo from claude.ai/code. Its changes reach your vault on the next pull. To avoid conflicts, let the plugin sync before and after asking Claude to edit notes.

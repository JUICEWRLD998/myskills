# Claude Code skills and plugins

Snapshot of the skills and plugins used with Claude Code, taken 2026-10-20.

- `skills/`: 53 skill folders, copied from `~/.claude/skills` (junctions resolved to real files).
- `plugins/`: user-scope plugin installs, copied from `~/.claude/plugins/cache`. Folder name is `<plugin>__<marketplace>`.
- `plugins/MANIFEST.json`: plugin, version and git commit of each copy.
- `plugins/known_marketplaces.json`: marketplaces to re-add.

## Restore

Skills:

    cp -r skills/* ~/.claude/skills/

Plugins: re-install from the marketplace at the pinned version (preferred):

    /plugin marketplace add <source from known_marketplaces.json>
    /plugin install <plugin>@<marketplace>

Or copy a folder into `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/` and register it in `installed_plugins.json`.

Mustapha Fadhlullah — independent security researcher

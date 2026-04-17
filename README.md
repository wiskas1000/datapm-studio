# datapm-studio

Web UI for [datapm](https://github.com/wiskas1000/data-project-manager) — form-based metadata management for analytical projects.

## What It Does

datapm-studio provides a local browser interface for managing project metadata that would be tedious to enter via CLI flags. Smart dropdowns for people and tags, a project creation wizard, and a close-out checklist that surfaces gaps in your metadata.

## Requirements

- Python 3.11+
- `data-project-manager` (the core datapm package)
- A configured datapm setup (`~/.datapm/config.json` and `~/.datapm/projects.db`)

## Install

datapm-studio is not yet published to PyPI. Install from source:

```bash
git clone https://github.com/wiskas1000/datapm-studio.git
cd datapm-studio
uv sync
```

## Usage

```bash
uv run datapm-studio
```

Serves on `http://127.0.0.1:5555`. Press Ctrl+C in the terminal to stop.

Override the bind address with `--host` / `--port` if 5555 is taken:

```bash
uv run datapm-studio --port 5556
uv run datapm-studio --host 0.0.0.0 --port 8080
```

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design document.

See [CLAUDE.md](CLAUDE.md) for Claude Code development instructions.

## Tech Stack

- **Flask** — server-rendered HTML
- **HTMX** — dynamic interactions without a JS framework
- **Custom CSS** — dark/light theme, DM Sans / DM Mono fonts
- **SQLite** — shared `projects.db` via datapm's repository layer

## Development

```bash
git clone https://github.com/wiskas1000/datapm-studio.git
cd datapm-studio
uv sync --extra dev
uv run pytest
```

# datapm-studio

Web UI for [datapm](https://github.com/your-username/data-project-manager) — form-based metadata management for analytical projects.

## What It Does

datapm-studio provides a local browser interface for managing project metadata that would be tedious to enter via CLI flags. Smart dropdowns for people and tags, a project creation wizard, and a close-out checklist that surfaces gaps in your metadata.

## Install

```bash
uv add datapm-studio
```

## Usage

```bash
datapm web
```

Opens a browser tab to `http://localhost:5555`. Press Ctrl+C in the terminal to stop.

```bash
datapm web --port 8080        # custom port
datapm web --no-browser       # don't auto-open browser
```

## Requirements

- Python 3.10+
- `data-project-manager` (the core datapm package)
- A configured datapm setup (`~/.datapm/config.json` and `~/.datapm/projects.db`)

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full design document.

See [CLAUDE.md](CLAUDE.md) for Claude Code development instructions.

## Tech Stack

- **Flask** — server-rendered HTML
- **HTMX** — dynamic interactions without a JS framework
- **Pico CSS** — classless CSS for clean defaults
- **SQLite** — shared `projects.db` via datapm's repository layer

## Development

```bash
git clone https://github.com/your-username/datapm-studio.git
cd datapm-studio
uv sync --extra dev
pytest
```

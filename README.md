# 🐍 Python Interactive Tutorial

Learn Python from fundamentals to AI engineering — all from your terminal.

## Quick Start

```bash
pip install python-tutorial

# Launch interactive mode
python-tutorial

# Or with the short alias
pytut
```

## Commands

| Command | Description |
|---------|-------------|
| `python-tutorial` | Interactive menu (default) |
| `python-tutorial list` | List all phases and topics |
| `python-tutorial view <phase> <topic>` | View a specific topic |
| `python-tutorial quiz [phase]` | Take a quiz (optional: specific phase) |
| `python-tutorial status` | Show learning progress |
| `python-tutorial reset` | Reset all progress |

## Features

- **56 topics** across 7 phases, from basics to AI engineering
- **Interactive reading** — sections displayed one at a time with code highlighting
- **Knowledge checks** — MCQ quizzes after each topic
- **Progress tracking** — saved to `~/.python_tutorial_progress.json`
- **Rich formatting** — syntax-highlighted code, panels, progress bars
- **Cross-platform** — works on Linux, macOS, Windows

## Content Structure

```
Phase 1: Python Fundamentals      (11 topics)
Phase 2: Core Python               (8 topics)
Phase 3: Object-Oriented Programming (8 topics)
Phase 4: Intermediate Python       (9 topics)
Phase 5: Advanced Python           (7 topics)
Phase 6: Python for Engineering    (6 topics)
Phase 7: Python for AI Engineering (7 topics)
```

## Custom Content Path

```bash
python-tutorial --content-dir /path/to/your/content
```

## Development

```bash
git clone <repo>
cd python-tutorial
pip install -e .
```

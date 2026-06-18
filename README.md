# Python Interactive Tutorial

Learn Python from fundamentals to AI engineering -- all from your terminal.

## Quick Start

```bash
pip install git+https://github.com/Manas-thakur/python-tutorial.git

# Launch interactive mode
pytut

# Or full command
python-tutorial
```

## Commands

| Command | Description |
|---------|-------------|
| `python-tutorial` | Interactive menu (default) |
| `list` | List all phases and topics |
| `view <phase> <topic>` | View a specific topic |
| `quiz [phase]` | Take a quiz (optional: specific phase) |
| `challenge <phase> <topic>` | Do a coding challenge |
| `projects` | Browse step-by-step project tutorials |
| `sandbox` | Open the code playground |
| `search <term>` | Search all content |
| `flashcards [phase]` | Review as flashcards |
| `status` | Show learning progress, level, streak, badges |
| `badges` | Show earned badges |
| `bookmark` | Show current bookmark |
| `reset` | Reset all progress |

## Features

- **56 topics** across 7 phases, from basics to AI engineering
- **7 project tutorials** -- 8-step guided walkthroughs (TUI editor, expense tracker, blog engine, chat server, task scheduler, pixel editor, API framework)
- **Interactive reading** -- sections displayed one at a time with syntax-highlighted code
- **Knowledge checks** -- Q&A review after each topic
- **Coding challenges** -- 150+ exercises with expected-output validation (easy/medium/hard)
- **Code sandbox** -- run Python code in an isolated subprocess (5s timeout, blocked imports)
- **Flashcards** -- Q&A review mode with self-rating
- **Full-text search** -- search across all topics
- **Progress tracking** -- saved to `~/.python_tutorial_progress.json`
- **XP & Level system** -- earn XP for completing topics and challenges, level up
- **Progressive unlocking** -- phases unlock at 70% completion of the previous phase
- **Project step tracking** -- per-step progress saved, step-locked navigation
- **Badges** -- 11+ badges for milestones, level milestones, and streaks
- **Streaks** -- consecutive daily usage tracking
- **Bookmark & resume** -- auto-bookmark, prompt to resume on next launch
- **Error explainer** -- plain-English explanations for common Python errors (13 types)
- **Rich formatting** -- syntax-highlighted code, panels, progress bars via Rich
- **Cross-platform** -- works on Linux, macOS, Windows

## Content Structure

```
Phase 1: Python Fundamentals          (11 topics)
Phase 2: Core Python                   (8 topics)
Phase 3: Object-Oriented Programming   (8 topics)
Phase 4: Intermediate Python           (9 topics)
Phase 5: Advanced Python               (7 topics)
Phase 6: Python for Engineering        (6 topics)
Phase 7: Python for AI Engineering     (7 topics)
Projects: 7 project tutorials          (8 steps each)
```

## Custom Content Path

```bash
python-tutorial --content-dir /path/to/your/content
```

## Project Tutorials (Codédex Submission)

Standalone step-by-step tutorials for building real projects from scratch. Each includes a starter skeleton and fully working solution:

| Project | Difficulty | README |
|---------|-----------|--------|
| TUI Text Editor | intermediate | [Read](./project-submissions/tui-text-editor/README.md) |
| Expense Tracker | beginner | [Read](./project-submissions/expense-tracker/README.md) |
| Markdown Blog Engine | intermediate | [Read](./project-submissions/markdown-blog/README.md) |
| Chat Server & Client | intermediate | [Read](./project-submissions/chat-server/README.md) |
| Task Scheduler | advanced | [Read](./project-submissions/task-scheduler/README.md) |
| Pixel Art Editor | intermediate | [Read](./project-submissions/pixel-editor/README.md) |
| API Framework | advanced | [Read](./project-submissions/api-framework/README.md) |

To run any project's solution: `cd project-submissions/<name>/solution && python <main_file>.py`

## Development

```bash
git clone https://github.com/Manas-thakur/python-tutorial.git
cd python-tutorial
pip install -e .
```

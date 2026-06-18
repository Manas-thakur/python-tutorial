"""Capture actual TUI screenshots using Textual's test/pilot API."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import cairosvg
from python_tutorial.content import discover_phases

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "banner")
os.makedirs(ASSETS_DIR, exist_ok=True)


async def _capture(app, pilot, name, wait=0.5):
    await asyncio.sleep(wait)
    svg_path = Path(ASSETS_DIR) / f"{name}.svg"
    app.save_screenshot(str(svg_path))
    cairosvg.svg2png(
        url=str(svg_path),
        output_width=1200,
        output_height=780,
        write_to=str(Path(ASSETS_DIR) / f"{name}.png"),
    )
    svg_path.unlink()
    print(f"  -> banner/{name}.png")


async def capture_main_screen():
    from python_tutorial.tui.app import TutorialApp

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await _capture(app, pilot, "tui-main")


async def capture_project_browser():
    from python_tutorial.tui.app import TutorialApp

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await pilot.press("f3")
        await _capture(app, pilot, "tui-projects")


async def capture_quiz():
    """Navigate to first topic, then open quiz so questions are available."""
    from python_tutorial.tui.app import TutorialApp

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await asyncio.sleep(0.3)
        phases = discover_phases()
        if phases and phases[0].topics:
            app._load_topic(phases[0], phases[0].topics[0])
            await asyncio.sleep(0.2)
        await pilot.press("ctrl+q")
        await _capture(app, pilot, "tui-quiz", wait=0.5)


async def capture_tutor():
    """Open the adaptive tutor dashboard."""
    from python_tutorial.tui.app import TutorialApp

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await asyncio.sleep(0.3)
        await pilot.press("ctrl+t")
        await _capture(app, pilot, "tui-tutor", wait=0.8)


async def capture_code_panel():
    """Show the CodePanel with code and running output visible."""
    from python_tutorial.tui.app import TutorialApp

    code_example = """def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        print(a, end=" ")
        a, b = b, a + b
    print()

fibonacci(10)"""

    from python_tutorial.tui.code_panel import CodePanel

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await asyncio.sleep(0.3)

        code_panel = app.query_one(CodePanel)
        editor = code_panel.query_one("#code-editor")
        editor.text = code_example
        editor.focus()
        editor.cursor = (0, 0)

        await asyncio.sleep(0.3)
        await _capture(app, pilot, "tui-code-panel")

    app2 = TutorialApp()
    async with app2.run_test(size=(90, 34)) as pilot2:
        await asyncio.sleep(0.3)
        code_panel2 = app2.query_one(CodePanel)
        editor2 = code_panel2.query_one("#code-editor")
        editor2.text = code_example
        editor2.focus()
        await asyncio.sleep(0.2)
        app2.action_run_code()
        await asyncio.sleep(0.5)
        await _capture(app2, pilot2, "tui-ide")


async def main():
    print("Capturing TUI screenshots...")

    print("  1. Main screen...")
    await capture_main_screen()

    print("  2. Project browser (F3)...")
    await capture_project_browser()

    print("  3. Quiz screen (Ctrl+Q)...")
    await capture_quiz()

    print("  4. Tutor dashboard (Ctrl+T)...")
    await capture_tutor()

    print("  5. Code panel with code...")
    await capture_code_panel()

    # Clean up SVG files
    for f in Path(ASSETS_DIR).glob("tui-*.svg"):
        f.unlink()

    print("\nDone! Check banner/ directory.")
    for f in sorted(Path(ASSETS_DIR).glob("tui-*.png")):
        size = f.stat().st_size
        print(f"  {f.name} ({size//1024}KB)")


if __name__ == "__main__":
    asyncio.run(main())

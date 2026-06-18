"""Capture actual TUI screenshots using Textual's test/pilot API."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import cairosvg

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


async def capture_sidebar_open():
    from python_tutorial.tui.app import TutorialApp

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await _capture(app, pilot, "tui-sidebar")


async def capture_quiz():
    from python_tutorial.tui.app import TutorialApp

    app = TutorialApp()
    async with app.run_test(size=(90, 34)) as pilot:
        await pilot.press("ctrl+q")
        await _capture(app, pilot, "tui-quiz")


async def main():
    print("Capturing TUI screenshots...")

    print("  1. Main screen...")
    await capture_main_screen()

    print("  2. Sidebar (phase list)...")
    await capture_sidebar_open()

    print("  3. Project browser (F3)...")
    await capture_project_browser()

    print("  4. Quiz screen (Ctrl+Q)...")
    await capture_quiz()

    # Clean up SVG files
    for f in Path(ASSETS_DIR).glob("tui-*.svg"):
        f.unlink()

    print("\nDone! Check banner/ directory.")
    for f in sorted(Path(ASSETS_DIR).glob("tui-*.png")):
        size = f.stat().st_size
        print(f"  {f.name} ({size//1024}KB)")


if __name__ == "__main__":
    asyncio.run(main())

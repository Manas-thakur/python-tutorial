from pathlib import Path
from typing import Optional

from .models import Phase, Topic, Section, QuizQuestion, ProjectTutorial

CONTENT_DIR = Path(__file__).parent / "content"


def _parse_sections(text: str) -> list[Section]:
    """Split markdown text into sections by ## headings."""
    sections: list[Section] = []
    lines = text.splitlines()
    current_heading: Optional[str] = None
    current_lines: list[str] = []

    for line in lines:
        if line.startswith("## "):
            if current_heading is not None:
                sections.append(
                    Section(
                        heading=current_heading,
                        content="\n".join(current_lines).strip(),
                    )
                )
            current_heading = line.removeprefix("## ").strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections.append(
            Section(
                heading=current_heading,
                content="\n".join(current_lines).strip(),
            )
        )

    return sections


def _parse_quiz_questions(section: Section) -> list[QuizQuestion]:
    """Parse knowledge-check Q&A from a section.

    Handles two formats:

    1. Simple Q&A (used in most files):
       1. Question text?
       2. Another question?

       **Answers:**
       1. Answer to question 1.
       2. Answer to question 2.

    2. MCQ format:
       1. Question?
          - [ ] Option A
          - [x] Option B
    """
    lines = section.content.splitlines()

    # Try MCQ format first
    questions = _try_parse_mcq(lines)
    if questions:
        return questions

    # Fallback to simple Q&A format
    return _try_parse_qa(lines)


def _try_parse_mcq(lines: list[str]) -> list[QuizQuestion]:
    questions: list[QuizQuestion] = []
    current_q: Optional[str] = None
    current_options: list[str] = []
    answer_idx: Optional[int] = None

    has_mcq_format = any(
        l.strip().startswith("- [") or l.strip().startswith("* [") for l in lines
    )
    if not has_mcq_format:
        return []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("- [") or stripped.startswith("* ["):
            option_text = stripped[4:].strip()
            is_answer = stripped.startswith("- [x]") or stripped.startswith("* [x]")
            current_options.append(option_text)
            if is_answer:
                answer_idx = len(current_options) - 1
        elif stripped[0].isdigit() and (". " in stripped or ") " in stripped):
            _flush_mcq(questions, current_q, current_options, answer_idx)
            current_options = []
            answer_idx = None
            after_num = stripped.split(". ", 1)
            current_q = after_num[1] if len(after_num) > 1 else stripped
        elif stripped.startswith("**") and "**" in stripped[2:]:
            _flush_mcq(questions, current_q, current_options, answer_idx)
            current_options = []
            answer_idx = None
            current_q = stripped.strip("*").strip()

    _flush_mcq(questions, current_q, current_options, answer_idx)
    return questions


def _flush_mcq(
    questions: list[QuizQuestion],
    q: Optional[str],
    opts: list[str],
    ans_idx: Optional[int],
):
    if q is not None and opts and ans_idx is not None:
        questions.append(
            QuizQuestion(question=q, answer=opts[ans_idx], options=list(opts), answer_index=ans_idx)
        )


def _try_parse_qa(lines: list[str]) -> list[QuizQuestion]:
    questions: list[QuizQuestion] = []
    question_map: dict[int, str] = {}
    answer_map: dict[int, str] = {}
    in_answers = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.lower().startswith("**answers") or stripped.lower().startswith("answers"):
            in_answers = True
            continue

        if not in_answers:
            _extract_qa_item(stripped, question_map)
        else:
            _extract_qa_item(stripped, answer_map)

    for num in sorted(question_map):
        if num in answer_map or question_map[num]:
            q_text = question_map[num]
            a_text = answer_map.get(num, "")
            if q_text:
                questions.append(QuizQuestion(question=q_text, answer=a_text))

    return questions


def _extract_qa_item(stripped: str, mapping: dict[int, str]):
    if stripped and stripped[0].isdigit():
        rest = stripped.split(". ", 1)
        rest2 = stripped.split(") ", 1)
        if len(rest) > 1:
            try:
                num = int(rest[0])
                mapping[num] = rest[1].strip()
            except ValueError:
                pass
        elif len(rest2) > 1:
            try:
                num = int(rest2[0])
                mapping[num] = rest2[1].strip()
            except ValueError:
                pass


def discover_phases(content_dir: Optional[Path] = None) -> list[Phase]:
    """Walk the content directory and build the phase/topic tree."""
    base = content_dir or CONTENT_DIR
    if not base.exists():
        return []
    phases: list[Phase] = []
    for d in sorted(base.iterdir()):
        if not d.is_dir():
            continue
        parts = d.name.split(" - ", 1)
        try:
            num = int(parts[0].split()[-1])
        except (ValueError, IndexError):
            num = 0
        title = parts[1] if len(parts) > 1 else d.name
        phase = Phase(number=num, title=title, path=d)
        md_files = sorted(d.glob("*.md"))
        for i, f in enumerate(md_files, start=1):
            name_parts = f.stem.split(". ", 1)
            topic_title = name_parts[1] if len(name_parts) > 1 else f.stem
            topic = Topic(number=i, title=topic_title, filepath=f)
            text = f.read_text(encoding="utf-8")
            topic.sections = _parse_sections(text)
            phase.topics.append(topic)
        phases.append(phase)
    return phases


def get_phase(number: int, content_dir: Optional[Path] = None) -> Optional[Phase]:
    for p in discover_phases(content_dir):
        if p.number == number:
            return p
    return None


def get_quiz_questions(topic: Topic) -> list[QuizQuestion]:
    for s in topic.sections:
        if s.heading.lower().strip() == "knowledge check":
            return _parse_quiz_questions(s)
    return []


def search_content(query: str, phases: list[Phase]) -> list[dict]:
    """Search across all topics for a query string. Case-insensitive."""
    results: list[dict] = []
    q = query.lower()
    for p in phases:
        for t in p.topics:
            text = t.filepath.read_text(encoding="utf-8")
            lines = text.splitlines()
            matches = [(i + 1, line.strip()) for i, line in enumerate(lines) if q in line.lower()]
            if matches:
                results.append({
                    "phase": p.number,
                    "topic": t.number,
                    "title": t.title,
                    "matches": matches[:20],  # cap per topic
                })
    return results


def get_revision_notes(topic: Topic) -> Optional[str]:
    """Extract the Revision notes section from a topic."""
    for s in topic.sections:
        if s.heading.lower().strip() == "revision notes":
            return s.content
    return None


def total_topics() -> int:
    """Return the total number of topics across all phases."""
    return sum(len(p.topics) for p in discover_phases())


def discover_project_tutorials() -> list[ProjectTutorial]:
    from .projects import load_all

    return load_all()



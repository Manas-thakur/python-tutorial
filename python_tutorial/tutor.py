"""Adaptive Tutor Engine - recommends optimal learning path based on mastery."""

from .content import discover_phases
from .progress import ProgressTracker


class TutorRecommendation:
    """A single recommendation."""
    def __init__(self, action_type: str, phase: int, topic: int, reason: str, priority: int):
        self.action_type = action_type  # 'learn', 'quiz', 'flashcard', 'challenge', 'review'
        self.phase = phase
        self.topic = topic
        self.reason = reason
        self.priority = priority  # Lower = higher priority

    def __lt__(self, other):
        return self.priority < other.priority


class AdaptiveTutor:
    """Generates personalized learning recommendations based on progress and mastery."""

    def __init__(self, progress: ProgressTracker):
        self.progress = progress
        self.phases = discover_phases()

    def get_next_recommendations(self, limit: int = 5) -> list[TutorRecommendation]:
        """
        Analyze progress and return top N recommendations for next action.
        Strategy:
        1. If no topics completed yet, recommend first topic in Phase 1.
        2. If weak topics exist, prioritize reviewing them with flashcards.
        3. If medium topics exist, recommend a quiz to solidify.
        4. If strong topics exist, suggest challenge or unlock next.
        5. Otherwise, suggest next unlocked topic.
        """
        recommendations = []

        # Gather all topics organized by mastery level
        weak_topics = []
        medium_topics = []
        strong_topics = []
        not_attempted = []

        for phase in self.phases:
            if not self.progress.is_phase_unlocked(phase.number):
                continue
            for topic in phase.topics:
                level = self.progress.get_topic_mastery_level(phase.number, topic.number)

                if level == "not_attempted":
                    not_attempted.append((phase.number, topic.number, topic.title))
                elif level == "weak":
                    weak_topics.append((phase.number, topic.number, topic.title))
                elif level == "medium":
                    medium_topics.append((phase.number, topic.number, topic.title))
                elif level == "strong":
                    strong_topics.append((phase.number, topic.number, topic.title))

        # Priority order:
        priority_counter = [0]

        # 1. Weak topics → flashcard review (highest priority)
        for phase, topic, title in weak_topics[:3]:
            priority_counter[0] += 1
            recommendations.append(
                TutorRecommendation(
                    "flashcard",
                    phase,
                    topic,
                    f"Review weak topic: {title}",
                    priority_counter[0],
                )
            )

        # 2. Medium topics → quiz to solidify
        for phase, topic, title in medium_topics[:2]:
            priority_counter[0] += 1
            recommendations.append(
                TutorRecommendation(
                    "quiz",
                    phase,
                    topic,
                    f"Solidify knowledge: {title}",
                    priority_counter[0],
                )
            )

        # 3. Not attempted → learn new
        for phase, topic, title in not_attempted[:3]:
            priority_counter[0] += 1
            recommendations.append(
                TutorRecommendation(
                    "learn",
                    phase,
                    topic,
                    f"Learn new topic: {title}",
                    priority_counter[0],
                )
            )

        # 4. Strong topics → challenge to apply
        for phase, topic, title in strong_topics[:1]:
            priority_counter[0] += 1
            recommendations.append(
                TutorRecommendation(
                    "challenge",
                    phase,
                    topic,
                    f"Apply skills: {title}",
                    priority_counter[0],
                )
            )

        # Sort by priority and return top N
        recommendations.sort()
        return recommendations[:limit]

    def get_phase_summary(self, phase_number: int) -> dict:
        """Get overview stats for a phase."""
        phase = next((p for p in self.phases if p.number == phase_number), None)
        if not phase:
            return {}

        total = len(phase.topics)
        completed = sum(
            1
            for t in phase.topics
            if self.progress.is_complete(phase_number, t.number)
        )
        strong = sum(
            1
            for t in phase.topics
            if self.progress.get_topic_mastery_level(phase_number, t.number)
            == "strong"
        )
        weak = sum(
            1
            for t in phase.topics
            if self.progress.get_topic_mastery_level(phase_number, t.number)
            == "weak"
        )

        return {
            "phase": phase_number,
            "title": phase.title,
            "total": total,
            "completed": completed,
            "strong": strong,
            "weak": weak,
            "unlocked": self.progress.is_phase_unlocked(phase_number),
            "progress": completed / total if total > 0 else 0,
        }

    def get_overall_stats(self) -> dict:
        """Get high-level learning stats."""
        total_topics = sum(len(p.topics) for p in self.phases)
        completed = self.progress.get_total_completed()
        weak_count = sum(
            1
            for phase in self.phases
            for topic in phase.topics
            if self.progress.get_topic_mastery_level(phase.number, topic.number)
            == "weak"
            and self.progress.is_complete(phase.number, topic.number)
        )
        strong_count = sum(
            1
            for phase in self.phases
            for topic in phase.topics
            if self.progress.get_topic_mastery_level(phase.number, topic.number)
            == "strong"
        )

        return {
            "total_topics": total_topics,
            "completed": completed,
            "completion_pct": (completed / total_topics * 100) if total_topics > 0 else 0,
            "strong": strong_count,
            "weak": weak_count,
            "level": self.progress.get_level(),
            "xp": self.progress.get_xp(),
            "streak": self.progress.get_streak(),
        }

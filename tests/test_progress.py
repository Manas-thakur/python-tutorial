

class TestProgressTracker:
    def test_initial_state(self, progress):
        assert progress.get_xp() == 0
        assert progress.get_level() == 0
        assert progress.get_total_completed() == 0
        assert progress.get_streak() == 0

    def test_mark_complete(self, progress):
        progress.mark_complete(1, 1)
        assert progress.is_complete(1, 1) is True
        assert progress.is_complete(1, 2) is False

    def test_add_xp_no_level_up(self, progress):
        result = progress.add_xp(10)
        assert result is False
        assert progress.get_xp() == 10

    def test_level_up(self, progress):
        result = progress.add_xp(200)
        assert result is True

    def test_bookmark(self, progress):
        progress.set_bookmark(1, 3, section_index=2)
        bm = progress.get_bookmark()
        assert bm["phase"] == 1
        assert bm["topic"] == 3
        assert bm["section"] == 2

        progress.clear_bookmark()
        assert progress.get_bookmark() is None

    def test_badges(self, progress):
        badges = progress.get_badges()
        assert isinstance(badges, list)

    def test_get_phase_progress(self, progress):
        done, total = progress.get_phase_progress(1, 10)
        assert done == 0
        assert total == 10

    def test_level_info(self, progress):
        info = progress.get_level_info()
        assert "level" in info
        assert "xp_current" in info
        assert "xp_needed" in info

    def test_mark_challenge(self, progress):
        progress.mark_challenge_done(2, 4, idx=0)
        assert progress.is_challenge_done(2, 4, 0) is True
        assert progress.is_challenge_done(2, 4, 1) is False

    def test_mastery(self, progress):
        progress.record_quiz_attempt(1, 1, 3, 5)
        score = progress.get_mastery_score(1, 1)
        assert score > 0
        assert score <= 1.0
        assert progress.get_topic_mastery_level(1, 1) in ("weak", "medium", "strong")

    def test_reset(self, progress):
        progress.add_xp(100)
        progress.mark_complete(1, 1)
        progress.reset()
        assert progress.get_xp() == 0
        assert progress.get_total_completed() == 0

    def test_streak(self, progress):
        progress.add_streak()
        assert progress.get_streak() >= 1

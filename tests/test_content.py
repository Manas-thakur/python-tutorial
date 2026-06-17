from python_tutorial.content import total_topics


class TestDiscoverPhases:
    def test_phases_loaded(self, phases):
        assert len(phases) > 0

    def test_phase_has_number_and_title(self, phases):
        for p in phases:
            assert p.number >= 1
            assert p.title

    def test_phase_has_topics(self, phases):
        for p in phases:
            assert len(p.topics) > 0

    def test_topic_has_title_and_sections(self, phases):
        for p in phases:
            for t in p.topics:
                assert t.title
                assert len(t.sections) > 0

    def test_section_has_heading_and_content(self, phases):
        for p in phases:
            for t in p.topics:
                for s in t.sections:
                    assert s.heading
                    assert s.content is not None


class TestTotalTopics:
    def test_total_topics_matches_sum(self, phases):
        manual = sum(len(p.topics) for p in phases)
        assert total_topics() == manual

    def test_total_topics_positive(self):
        assert total_topics() > 0

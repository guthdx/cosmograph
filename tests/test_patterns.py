"""Unit tests for pattern configuration."""


import pytest
from pydantic import ValidationError

from cosmograph.config import (
    EntityPattern,
    PatternConfig,
    RelationshipTrigger,
    load_default_patterns,
    load_patterns,
)
from cosmograph.extractors import GenericExtractor


class TestEntityPattern:
    """Tests for EntityPattern model validation."""

    def test_valid_pattern_with_one_capture_group(self):
        """Pattern with exactly one capture group should pass."""
        ep = EntityPattern(
            name="test",
            pattern=r"([a-z]+)",
            category="test"
        )
        assert ep.name == "test"
        assert ep.pattern == r"([a-z]+)"

    def test_invalid_regex_syntax(self):
        """Pattern with invalid regex syntax should fail."""
        with pytest.raises(ValidationError) as exc_info:
            EntityPattern(name="bad", pattern=r"[", category="test")
        assert "Invalid regex" in str(exc_info.value)

    def test_zero_capture_groups(self):
        """Pattern with no capture groups should fail."""
        with pytest.raises(ValidationError) as exc_info:
            EntityPattern(name="no_group", pattern=r"[a-z]+", category="test")
        assert "capture group" in str(exc_info.value).lower()

    def test_multiple_capture_groups(self):
        """Pattern with multiple capture groups should fail."""
        with pytest.raises(ValidationError) as exc_info:
            EntityPattern(name="multi", pattern=r"([a-z]+)([0-9]+)", category="test")
        assert "capture group" in str(exc_info.value).lower()

    def test_non_capturing_groups_allowed(self):
        """Non-capturing groups (?:...) should not count."""
        ep = EntityPattern(
            name="with_non_capturing",
            pattern=r"(?:Mr|Mrs)\s+([A-Z][a-z]+)",
            category="person"
        )
        assert ep.pattern == r"(?:Mr|Mrs)\s+([A-Z][a-z]+)"

    def test_default_values(self):
        """Default values should be applied."""
        ep = EntityPattern(name="test", pattern=r"([a-z]+)", category="test")
        assert ep.description == ""
        assert ep.min_length == 2


class TestRelationshipTrigger:
    """Tests for RelationshipTrigger model."""

    def test_valid_trigger(self):
        rt = RelationshipTrigger(
            name="mentions",
            source_categories=["document"],
            target_categories=["entity"]
        )
        assert rt.proximity == 0
        assert rt.trigger_pattern is None

    def test_with_trigger_pattern(self):
        rt = RelationshipTrigger(
            name="defines",
            source_categories=["section"],
            target_categories=["term"],
            trigger_pattern=r"means|shall mean"
        )
        assert rt.trigger_pattern == r"means|shall mean"


class TestPatternConfig:
    """Tests for PatternConfig model."""

    def test_valid_config(self, valid_pattern_config):
        config = PatternConfig.model_validate(valid_pattern_config)
        assert config.version == "1.0"
        assert len(config.entity_patterns) == 2
        assert len(config.relationship_triggers) == 1

    def test_minimal_config(self):
        """Minimal config with just required fields."""
        config = PatternConfig.model_validate({
            "entity_patterns": [
                {"name": "test", "pattern": r"([a-z]+)", "category": "test"}
            ]
        })
        assert config.version == "1.0"
        assert config.min_occurrences == 2
        assert config.relationship_triggers == []

    def test_config_with_invalid_pattern(self):
        """Config with invalid regex should fail validation."""
        with pytest.raises(ValidationError):
            PatternConfig.model_validate({
                "entity_patterns": [
                    {"name": "bad", "pattern": "[invalid", "category": "test"}
                ]
            })


class TestLoadPatterns:
    """Tests for load_patterns function."""

    def test_load_valid_file(self, create_pattern_file, valid_pattern_config):
        filepath = create_pattern_file("valid.yaml", valid_pattern_config)
        config = load_patterns(filepath)
        assert config.name == "test-patterns"
        assert len(config.entity_patterns) == 2

    def test_load_invalid_yaml_syntax(self, tmp_path):
        """Invalid YAML syntax should raise ValueError."""
        filepath = tmp_path / "invalid.yaml"
        filepath.write_text("{ unclosed: bracket")
        with pytest.raises(ValueError) as exc_info:
            load_patterns(filepath)
        assert "Invalid YAML" in str(exc_info.value) or "YAML" in str(exc_info.value)

    def test_load_empty_file(self, tmp_path):
        """Empty file should raise ValueError."""
        filepath = tmp_path / "empty.yaml"
        filepath.write_text("")
        with pytest.raises(ValueError) as exc_info:
            load_patterns(filepath)
        assert "Empty" in str(exc_info.value)

    def test_load_invalid_pattern_in_file(self, create_pattern_file):
        """File with invalid regex should raise ValidationError."""
        config = {
            "entity_patterns": [
                {"name": "bad", "pattern": "[invalid", "category": "test"}
            ]
        }
        filepath = create_pattern_file("bad_regex.yaml", config)
        with pytest.raises(ValidationError):
            load_patterns(filepath)


class TestLoadDefaultPatterns:
    """Tests for load_default_patterns function."""

    def test_loads_successfully(self):
        config = load_default_patterns()
        assert isinstance(config, PatternConfig)
        assert config.name == "default"

    def test_has_expected_patterns(self):
        config = load_default_patterns()
        pattern_names = {ep.name for ep in config.entity_patterns}
        assert "proper_noun" in pattern_names
        assert "acronym" in pattern_names
        assert "quoted_term" in pattern_names
        assert "section_ref" in pattern_names

    def test_patterns_are_valid_regex(self):
        """All default patterns should be valid."""
        import re
        config = load_default_patterns()
        for ep in config.entity_patterns:
            compiled = re.compile(ep.pattern)
            assert compiled.groups == 1


class TestGenericExtractorWithPatternConfig:
    """Tests for GenericExtractor integration with PatternConfig patterns.

    Note: Tests use the existing patterns dict interface since GenericExtractor
    does not yet accept PatternConfig directly (planned for 03-02). These tests
    verify that PatternConfig patterns can be converted to the dict format that
    GenericExtractor accepts.
    """

    def test_extracts_with_patterns_from_config(self, tmp_path, valid_pattern_config):
        """PatternConfig patterns can be converted to extractor dict format."""
        # Create test document
        doc = tmp_path / "test.txt"
        doc.write_text("Contact us at test@example.com or call 555-123-4567.")

        # Load and convert config to patterns dict
        config = PatternConfig.model_validate(valid_pattern_config)
        patterns_dict = {ep.name: ep.pattern for ep in config.entity_patterns}

        # Extract using dict interface
        extractor = GenericExtractor(patterns=patterns_dict, min_occurrences=config.min_occurrences)
        graph = extractor.extract(doc)

        # Should find email and phone
        labels = [n.label for n in graph.nodes.values()]
        assert any("test@example.com" in label for label in labels)
        assert any("555-123-4567" in label for label in labels)

    def test_config_min_occurrences_works(self, tmp_path):
        """min_occurrences from config is respected."""
        config = PatternConfig.model_validate({
            "min_occurrences": 3,
            "entity_patterns": [
                {"name": "word", "pattern": r"\b([A-Z][a-z]+)\b", "category": "word"}
            ]
        })

        doc = tmp_path / "test.txt"
        doc.write_text("Alpha Beta Alpha Alpha Gamma")

        # Convert to dict and use config's min_occurrences
        patterns_dict = {ep.name: ep.pattern for ep in config.entity_patterns}
        extractor = GenericExtractor(patterns=patterns_dict, min_occurrences=config.min_occurrences)
        graph = extractor.extract(doc)

        labels = [n.label for n in graph.nodes.values()]
        # Alpha appears 3 times, should be included
        assert any("Alpha" in label for label in labels)
        # Beta and Gamma appear less than 3 times, should not be included
        assert not any(label == "Beta" for label in labels)
        assert not any(label == "Gamma" for label in labels)

    def test_pattern_category_in_config(self, tmp_path):
        """Pattern category can be different from pattern name in config."""
        config = PatternConfig.model_validate({
            "min_occurrences": 1,
            "entity_patterns": [
                {
                    "name": "email_pattern",
                    "pattern": r"([a-z]+@[a-z]+\.com)",
                    "category": "contact_email",
                }
            ]
        })

        # Verify category is stored in config
        assert config.entity_patterns[0].name == "email_pattern"
        assert config.entity_patterns[0].category == "contact_email"

        # Note: Current GenericExtractor uses pattern name as category when using dict interface
        # Category mapping will work when config= parameter is added in 03-02

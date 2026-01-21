"""Pydantic models for YAML-based pattern configuration."""

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, field_validator


class EntityPattern(BaseModel):
    """Configuration for a single entity extraction pattern."""

    name: str
    pattern: str
    category: str
    description: str = ""
    min_length: int = 2

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Validate that pattern is valid regex with exactly one capture group."""
        try:
            compiled = re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e

        if compiled.groups == 0:
            raise ValueError("Pattern must have exactly one capture group, got 0")
        if compiled.groups > 1:
            raise ValueError(f"Pattern must have exactly one capture group, got {compiled.groups}")

        return v


class RelationshipTrigger(BaseModel):
    """Configuration for relationship creation triggers."""

    name: str
    source_categories: list[str]
    target_categories: list[str]
    proximity: int = 0
    trigger_pattern: str | None = None


class PatternConfig(BaseModel):
    """Root configuration for pattern-based extraction."""

    version: str = "1.0"
    name: str = "default"
    description: str = ""
    min_occurrences: int = 2
    entity_patterns: list[EntityPattern]
    relationship_triggers: list[RelationshipTrigger] = []


def load_patterns(filepath: Path) -> PatternConfig:
    """Load pattern configuration from a YAML file.

    Args:
        filepath: Path to the YAML configuration file.

    Returns:
        Validated PatternConfig instance.

    Raises:
        FileNotFoundError: If the file doesn't exist.
        ValueError: If the YAML is invalid or patterns fail validation.
    """
    yaml_content = filepath.read_text(encoding="utf-8")
    raw_data: Any = yaml.safe_load(yaml_content)
    return PatternConfig.model_validate(raw_data)


def load_default_patterns() -> PatternConfig:
    """Load the bundled default patterns.

    Returns:
        Validated PatternConfig with default extraction patterns.
    """
    from importlib.resources import files

    yaml_content = files("cosmograph.config").joinpath("default_patterns.yaml").read_text()
    raw_data: Any = yaml.safe_load(yaml_content)
    return PatternConfig.model_validate(raw_data)

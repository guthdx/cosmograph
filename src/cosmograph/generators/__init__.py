"""Output generators for knowledge graphs."""

from .csv import CSVGenerator
from .html import HTMLGenerator

__all__ = ["HTMLGenerator", "CSVGenerator"]

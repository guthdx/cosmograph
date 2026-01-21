"""Legal document extractor for codes, ordinances, and constitutions."""

import re
from pathlib import Path
from typing import Optional

from ..models import Graph
from .base import BaseExtractor


class LegalDocumentExtractor(BaseExtractor):
    """Extract entities from legal documents (codes, ordinances, constitutions)."""

    # Key entities commonly found in legal documents
    KEY_ENTITIES = {
        "Tribal Council": ("authority", "Governing body of the tribe"),
        "Tribal Court": ("authority", "Judicial body of the tribe"),
        "Tribal Chairman": ("authority", "Elected leader"),
        "Chief Judge": ("authority", "Head of court system"),
    }

    def supports(self, filepath: Path) -> bool:
        # Legal documents are typically text files with specific naming
        return filepath.suffix.lower() in {".txt", ".md"}

    def extract(self, filepath: Path) -> Graph:
        """Extract entities from a legal document."""
        text = self.read_text(filepath)
        source_name = filepath.stem

        # Determine document type based on content/name
        doc_type = self._determine_document_type(source_name, text)

        # Add document as root node
        doc_id = self.graph.add_node(
            source_name, source_name, doc_type, f"Legal document: {filepath.name}", filepath.name
        )

        # Extract based on document type
        if doc_type == "constitution":
            self._extract_constitution(text, doc_id, filepath.name)
        elif doc_type == "ordinance":
            self._extract_ordinance(text, doc_id, filepath.name)
        else:
            self._extract_code(text, doc_id, filepath.name)

        # Extract key entities referenced
        self._extract_key_entities(text, doc_id)

        return self.graph

    def _determine_document_type(self, name: str, text: str) -> str:
        """Determine the type of legal document."""
        name_lower = name.lower()
        text_lower = text[:2000].lower()

        if "constitution" in name_lower or "constitution" in text_lower:
            return "constitution"
        elif "ordinance" in name_lower:
            return "ordinance"
        else:
            return "code"

    def _extract_constitution(self, text: str, doc_id: str, source: str) -> None:
        """Extract from constitutional documents."""
        # Articles
        for match in re.finditer(r"ARTICLE\s+([IVX]+)[—\-\s]+([A-Z\s]+)", text):
            article_num = match.group(1)
            article_title = match.group(2).strip().title()
            article_id = self.graph.add_node(
                f"Article {article_num}",
                f"Article {article_num} - {article_title}",
                "article",
                article_title,
                source,
            )
            self.graph.add_edge(doc_id, article_id, "contains")

        # Sections
        for match in re.finditer(r"(?:SECTION|SEC\.?)\s+(\d+)\.", text):
            section_num = match.group(1)
            section_id = self.graph.add_node(
                f"Section {section_num}", f"Section {section_num}", "section", "", source
            )
            self.graph.add_edge(doc_id, section_id, "contains")

    def _extract_ordinance(self, text: str, doc_id: str, source: str) -> None:
        """Extract from ordinance documents."""
        # Sections in ordinances
        for match in re.finditer(r"Section\s+(\d+)[.:\s]+([A-Za-z\s]+)", text):
            section_num = match.group(1)
            section_title = match.group(2).strip()[:50]
            section_id = self.graph.add_node(
                f"{source} Sec {section_num}",
                f"Section {section_num} - {section_title}",
                "section",
                section_title,
                source,
            )
            self.graph.add_edge(doc_id, section_id, "contains")

    def _extract_code(self, text: str, doc_id: str, source: str) -> None:
        """Extract from code documents."""
        # Titles
        for match in re.finditer(r"TITLE\s+([IVXLC\d]+)[:\s—\-]+([A-Z\s]+)", text):
            title_num = match.group(1)
            title_name = match.group(2).strip().title()[:40]
            title_id = self.graph.add_node(
                f"Title {title_num} - {title_name}",
                f"Title {title_num} - {title_name}",
                "title",
                title_name,
                source,
            )
            self.graph.add_edge(doc_id, title_id, "contains")

        # Chapters
        for match in re.finditer(r"CHAPTER\s+([IVXLC\d]+)[,:\s—\-]+([A-Z\s]+)", text):
            chapter_num = match.group(1)
            chapter_name = match.group(2).strip().title()[:40]
            chapter_id = self.graph.add_node(
                f"Chapter {chapter_num} - {chapter_name}",
                f"Chapter {chapter_num} - {chapter_name}",
                "chapter",
                chapter_name,
                source,
            )
            self.graph.add_edge(doc_id, chapter_id, "contains")

        # Offenses
        offense_patterns = [
            r"(?:guilty of|commits?) (?:the offense of |an offense of )?([A-Za-z\s]+?)(?:\s+if|\s+when|\s+shall)",
        ]
        for pattern in offense_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                offense_name = match.group(1).strip().title()
                if 5 < len(offense_name) < 50:
                    offense_id = self.graph.add_node(
                        offense_name,
                        offense_name,
                        "offense",
                        f"Offense defined in {source}",
                        source,
                    )
                    self.graph.add_edge(doc_id, offense_id, "defines")

        # Definitions
        for match in re.finditer(
            r'"([A-Za-z\s]+)"\s+(?:means|shall mean|is defined as)\s+([^.]+)', text
        ):
            term = match.group(1).strip().title()
            definition = match.group(2).strip()[:100]
            if 2 < len(term) < 40:
                def_id = self.graph.add_node(term, term, "definition", definition, source)
                self.graph.add_edge(doc_id, def_id, "defines")

    def _extract_key_entities(self, text: str, doc_id: str) -> None:
        """Extract references to key legal entities."""
        text_lower = text.lower()
        for entity, (category, description) in self.KEY_ENTITIES.items():
            if entity.lower() in text_lower:
                entity_id = self.graph.add_node(entity, entity, category, description, "")
                self.graph.add_edge(doc_id, entity_id, "references")

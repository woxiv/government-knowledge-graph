from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ParsedDocument:
    url: str
    page_type: str
    title: Optional[str] = None
    publish_time: Optional[str] = None
    source: Optional[str] = None
    content: Optional[str] = None
    raw_html: Optional[str] = None
    discovered_urls: list[str] = field(default_factory=list)


@dataclass
class Entity:
    name: str
    type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    source: str
    source_type: str
    relation: str
    target: str
    target_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    doc_id: str
    extractor_name: str
    extractor_version: str
    entities: list[Entity]
    relations: list[Relation]

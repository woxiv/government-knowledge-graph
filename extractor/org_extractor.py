from bs4 import BeautifulSoup
from models import Entity, Relation, ExtractionResult


def extract_org_directory(doc_id: str, html: str) -> ExtractionResult:
    soup = BeautifulSoup(html, "html.parser")

    entities: list[Entity] = []
    relations: list[Relation] = []

    region_name = "浑源县"

    entities.append(Entity(
        name=region_name,
        type="Region",
        properties={}
    ))

    current_type = None

    for node in soup.find_all(["a", "span", "div", "li", "p"]):
        text = node.get_text(strip=True)

        if not text:
            continue

        if text == "政府部门":
            current_type = "政府部门"
            continue

        if text == "乡镇街道":
            current_type = "乡镇街道"
            continue

        if node.name != "a":
            continue

        href = node.get("href")
        if not href:
            continue

        if current_type not in ["政府部门", "乡镇街道"]:
            continue

        org_name = text

        entities.append(Entity(
            name=org_name,
            type="Organization",
            properties={
                "org_type": current_type,
                "source_url": href,
            }
        ))

        relation_name = "包含政府部门" if current_type == "政府部门" else "下辖乡镇"

        relations.append(Relation(
            source=region_name,
            source_type="Region",
            relation=relation_name,
            target=org_name,
            target_type="Organization",
            properties={
                "evidence_doc_id": doc_id,
            }
        ))

    return ExtractionResult(
        doc_id=doc_id,
        extractor_name="org_directory_extractor",
        extractor_version="v1",
        entities=entities,
        relations=relations,
    )
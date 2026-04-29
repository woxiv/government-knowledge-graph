from models import Entity, Relation, ExtractionResult


def extract_article(doc_id: str, title: str, content: str, source: str | None = None) -> ExtractionResult:
    entities: list[Entity] = []
    relations: list[Relation] = []

    if title:
        entities.append(Entity(
            name=title,
            type="Policy",
            properties={}
        ))

    if source:
        entities.append(Entity(
            name=source,
            type="Organization",
            properties={}
        ))

        relations.append(Relation(
            source=source,
            source_type="Organization",
            relation="发布",
            target=title,
            target_type="Policy",
            properties={
                "evidence_doc_id": doc_id,
            }
        ))

    # 简单规则：正文里出现这些词，就作为事项实体
    matter_keywords = ["补贴", "申报", "审批", "备案", "许可", "救助", "登记"]

    for keyword in matter_keywords:
        if keyword in content:
            entities.append(Entity(
                name=keyword,
                type="Matter",
                properties={}
            ))

            relations.append(Relation(
                source=title,
                source_type="Policy",
                relation="涉及",
                target=keyword,
                target_type="Matter",
                properties={
                    "evidence_doc_id": doc_id,
                }
            ))

    return ExtractionResult(
        doc_id=doc_id,
        extractor_name="article_rule_extractor",
        extractor_version="v1",
        entities=entities,
        relations=relations,
    )

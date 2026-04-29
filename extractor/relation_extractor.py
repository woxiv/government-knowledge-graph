from __future__ import annotations

import re
from typing import List, Tuple

from extractor.normalizer import make_rel_id


def extract_subordinate_relations(
    doc_id: str,
    text: str,
    org_ids_by_name: dict[str, str],
) -> List[dict]:
    edges = []
    text_normalized = re.sub(r"\s+", "", text or "")

    county_gov_name = "浑源县人民政府"
    county_gov_id = org_ids_by_name.get(county_gov_name)

    if not county_gov_id:
        return edges

    for name, org_id in org_ids_by_name.items():
        if name == county_gov_name:
            continue
        if name not in text_normalized:
            continue

        # 规则1：浑源县XX局 / 委 / 政府办公室 默认是县政府工作部门候选
        if name.startswith("浑源县") and any(k in name for k in ["局", "委员会", "人民政府办公室"]):
            edges.append({
                "rel_id": make_rel_id(org_id, county_gov_id, "SUBORDINATE_TO"),
                "from_org_id": org_id,
                "to_org_id": county_gov_id,
                "relation_type": "SUBORDINATE_TO",
                "evidence_doc_ids": [doc_id],
                "evidence_text": f"{name}出现在浑源县政府官网组织/政务公开页面中，规则判定为县级政府工作部门候选。",
                "confidence": 0.82,
                "scenario_tags": ["组织机构"],
            })

        # 规则2：大同市XX局浑源分局 -> 大同市XX局
        if name.startswith("大同市") and "浑源分局" in name:
            parent_name = name.split("浑源分局")[0]
            parent_id = org_ids_by_name.get(parent_name)
            if parent_id:
                edges.append({
                    "rel_id": make_rel_id(org_id, parent_id, "SUBORDINATE_TO"),
                    "from_org_id": org_id,
                    "to_org_id": parent_id,
                    "relation_type": "SUBORDINATE_TO",
                    "evidence_doc_ids": [doc_id],
                    "evidence_text": f"{name}命名模式符合“市局+县域分局”，规则判定为上级市局分支机构。",
                    "confidence": 0.88,
                    "scenario_tags": ["垂直管理"],
                })

    return edges

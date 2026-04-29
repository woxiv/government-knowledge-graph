from __future__ import annotations


def classify_org_type(name: str) -> str:
    if any(k in name for k in ["局", "委员会", "政府办公室", "分局", "派出所"]):
        return "gov_dept"
    if any(k in name for k in ["医院", "学校", "中心", "研究院", "融媒体中心", "服务中心"]):
        return "institution"
    if any(k in name for k in ["集团", "有限公司", "有限责任公司"]):
        return "soe"
    if any(k in name for k in ["协会", "学会", "联合会", "促进会"]):
        return "social_org"
    return "gov_dept"


def classify_admin_level(name: str) -> str | None:
    if "山西省" in name:
        return "province"
    if "大同市" in name and "浑源分局" not in name:
        return "city"
    if "浑源县" in name or "浑源分局" in name:
        return "district_county"
    if any(k in name for k in ["乡", "镇", "街道"]):
        return "township"
    return None


def classify_org_rank(name: str, org_type: str) -> str | None:
    if name.endswith("人民政府"):
        return "government"
    if "分局" in name or "派出所" in name:
        return "branch"
    if any(k in name for k in ["局", "委员会", "政府办公室"]):
        return "bureau"
    if org_type == "institution":
        return "institution"
    if any(k in name for k in ["股", "室", "科"]):
        return "section"
    return None
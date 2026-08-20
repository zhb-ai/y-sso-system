"""企业微信成员扩展属性 / 手机号解析"""

import re
from typing import Any, Dict, Optional, Tuple

# 中国大陆手机号
MOBILE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")


def extattr_value(user: Dict[str, Any], attr_name: str) -> Optional[str]:
    """从成员 extattr 中读取指定名称的文本扩展属性"""
    attrs = ((user.get("extattr") or {}).get("attrs")) or []
    for attr in attrs:
        if attr.get("name") != attr_name:
            continue
        value = attr.get("value")
        if value:
            return str(value).strip() or None
        text = (attr.get("text") or {}).get("value")
        if text:
            return str(text).strip() or None
    return None


def extract_id_card(user: Dict[str, Any]) -> Optional[str]:
    """从企微成员详情中提取身份证号（扩展属性「身份证号」）"""
    return extattr_value(user, "身份证号")


def extract_mobile(user: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    """提取手机号，返回 (mobile, source)。

    企微通讯录接口的 mobile 字段经常为空，实际号码常写在
    telephone / alias / english_name / name 或扩展属性「手机号」中。
    优先级：mobile → 扩展属性「手机号」→ telephone → alias → english_name → name
    """
    mobile = (user.get("mobile") or "").strip()
    if mobile and MOBILE_RE.fullmatch(mobile):
        return mobile, "mobile"
    if mobile:
        match = MOBILE_RE.search(mobile)
        if match:
            return match.group(1), "mobile"

    ext_mobile = extattr_value(user, "手机号")
    if ext_mobile:
        match = MOBILE_RE.search(ext_mobile)
        if match:
            return match.group(1), "extattr:手机号"

    for field in ("telephone", "alias", "english_name", "name"):
        text = (user.get(field) or "").strip()
        if not text:
            continue
        match = MOBILE_RE.search(text)
        if match:
            return match.group(1), field
    return None, None


def normalize_mobile(user: Dict[str, Any]) -> Optional[str]:
    """提取企微成员手机号（仅返回号码本身）"""
    mobile, _ = extract_mobile(user)
    return mobile

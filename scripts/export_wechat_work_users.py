#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按部门导出企业微信全员信息到 JSON，并标出缺失手机号/身份证号的用户。

用法:
  python scripts/export_wechat_work_users.py --corp-id wwa... --corp-secret 'xxx'
  python scripts/export_wechat_work_users.py  # 也可读环境变量 WECHAT_CORP_ID / WECHAT_CORP_SECRET
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "scripts", "output", "wechat_work_users.json")
DEFAULT_MISSING_OUT = os.path.join(
    ROOT, "scripts", "output", "wechat_work_users_missing.json"
)

MOBILE_RE = re.compile(r"(?<!\d)(1[3-9]\d{9})(?!\d)")


def _http_get_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_access_token(corp_id: str, corp_secret: str) -> str:
    url = "https://qyapi.weixin.qq.com/cgi-bin/gettoken?" + urllib.parse.urlencode(
        {"corpid": corp_id, "corpsecret": corp_secret}
    )
    data = _http_get_json(url)
    if data.get("errcode", 0) != 0 or not data.get("access_token"):
        raise RuntimeError(
            f"gettoken 失败: errcode={data.get('errcode')} errmsg={data.get('errmsg')}"
        )
    return data["access_token"]


def list_departments(access_token: str) -> List[dict]:
    url = "https://qyapi.weixin.qq.com/cgi-bin/department/list?" + urllib.parse.urlencode(
        {"access_token": access_token}
    )
    data = _http_get_json(url)
    if data.get("errcode", 0) != 0:
        raise RuntimeError(
            f"department/list 失败: errcode={data.get('errcode')} errmsg={data.get('errmsg')}"
        )
    return data.get("department") or []


def list_department_users(access_token: str, department_id: int) -> List[dict]:
    url = "https://qyapi.weixin.qq.com/cgi-bin/user/list?" + urllib.parse.urlencode(
        {
            "access_token": access_token,
            "department_id": department_id,
        }
    )
    data = _http_get_json(url)
    if data.get("errcode", 0) != 0:
        raise RuntimeError(
            f"user/list 失败 (dept={department_id}): "
            f"errcode={data.get('errcode')} errmsg={data.get('errmsg')}"
        )
    return data.get("userlist") or []


def _extattr_value(user: dict, attr_name: str) -> Optional[str]:
    attrs = ((user.get("extattr") or {}).get("attrs")) or []
    for attr in attrs:
        if attr.get("name") == attr_name:
            value = attr.get("value")
            if value:
                return str(value).strip()
            text = (attr.get("text") or {}).get("value")
            if text:
                return str(text).strip()
    return None


def extract_mobile(user: dict) -> Tuple[Optional[str], Optional[str]]:
    """返回 (mobile, mobile_source)。

    优先级：mobile → telephone → alias → english_name → name
    （企微常把手机号填在 telephone / 姓名 / 别名，而不在 mobile）
    """
    mobile = (user.get("mobile") or "").strip()
    if mobile:
        return mobile, "mobile"

    for field in ("telephone", "alias", "english_name", "name"):
        text = (user.get(field) or "").strip()
        if not text:
            continue
        match = MOBILE_RE.search(text)
        if match:
            return match.group(1), field
    return None, None


def extract_id_card(user: dict) -> Optional[str]:
    return _extattr_value(user, "身份证号") or None


def simplify_user(user: dict, dept_id: int) -> dict:
    mobile, mobile_source = extract_mobile(user)
    id_card = extract_id_card(user)
    return {
        "userid": user.get("userid"),
        "name": user.get("name"),
        "department": user.get("department") or [],
        "main_department": user.get("main_department"),
        "listed_in_department": dept_id,
        "position": user.get("position") or _extattr_value(user, "职位") or "",
        "status": user.get("status"),
        "enable": user.get("enable"),
        "telephone": user.get("telephone") or "",
        "alias": user.get("alias") or "",
        "english_name": user.get("english_name") or "",
        "mobile": mobile,
        "mobile_source": mobile_source,
        "id_card": id_card,
        "has_mobile": bool(mobile),
        "has_id_card": bool(id_card),
        "extattr": (user.get("extattr") or {}).get("attrs") or [],
    }


def missing_summary_item(user: dict) -> dict:
    return {
        "userid": user.get("userid"),
        "name": user.get("name"),
        "main_department": user.get("main_department"),
        "department": user.get("department") or [],
        "mobile": user.get("mobile"),
        "mobile_source": user.get("mobile_source"),
        "id_card": user.get("id_card"),
        "has_mobile": user.get("has_mobile"),
        "has_id_card": user.get("has_id_card"),
    }


def build_missing_payload(result: dict, source_path: str) -> dict:
    missing_mobile = result.get("missing_mobile") or []
    missing_id_card = result.get("missing_id_card") or []
    missing_both = result.get("missing_both") or []

    seen = set()
    missing_any = []
    for item in missing_mobile + missing_id_card:
        userid = item.get("userid")
        if userid in seen:
            continue
        seen.add(userid)
        missing_any.append(item)

    return {
        "exported_at": result.get("exported_at"),
        "source": source_path,
        "corp_id": result.get("corp_id"),
        "summary": {
            "unique_user_count": (result.get("summary") or {}).get("unique_user_count"),
            "missing_mobile_count": len(missing_mobile),
            "missing_id_card_count": len(missing_id_card),
            "missing_both_count": len(missing_both),
            "missing_any_count": len(missing_any),
        },
        "missing_mobile": missing_mobile,
        "missing_id_card": missing_id_card,
        "missing_both": missing_both,
        "missing_any": missing_any,
    }


def export_users(
    corp_id: str,
    corp_secret: str,
    out_path: str,
    missing_out_path: Optional[str] = None,
) -> dict:
    access_token = get_access_token(corp_id, corp_secret)
    departments = list_departments(access_token)

    dept_payload: List[dict] = []
    unique_users: Dict[str, dict] = {}

    for dept in departments:
        dept_id = dept["id"]
        raw_users = list_department_users(access_token, dept_id)
        simplified = [simplify_user(u, dept_id) for u in raw_users]
        for item in simplified:
            userid = item.get("userid")
            if userid and userid not in unique_users:
                unique_users[userid] = item

        dept_payload.append(
            {
                "id": dept_id,
                "name": dept.get("name"),
                "parentid": dept.get("parentid"),
                "order": dept.get("order"),
                "user_count": len(simplified),
                "users": simplified,
            }
        )

    all_users = list(unique_users.values())
    missing_mobile = [missing_summary_item(u) for u in all_users if not u.get("has_mobile")]
    missing_id_card = [missing_summary_item(u) for u in all_users if not u.get("has_id_card")]
    missing_both = [
        missing_summary_item(u)
        for u in all_users
        if (not u.get("has_mobile")) and (not u.get("has_id_card"))
    ]

    result = {
        "exported_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "corp_id": corp_id,
        "summary": {
            "department_count": len(departments),
            "unique_user_count": len(all_users),
            "missing_mobile_count": len(missing_mobile),
            "missing_id_card_count": len(missing_id_card),
            "missing_both_count": len(missing_both),
        },
        "departments": dept_payload,
        "users_unique": all_users,
        "missing_mobile": missing_mobile,
        "missing_id_card": missing_id_card,
        "missing_both": missing_both,
    }

    out_dir = os.path.dirname(os.path.abspath(out_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if missing_out_path is None:
        base, ext = os.path.splitext(out_path)
        missing_out_path = f"{base}_missing{ext or '.json'}"
    missing_payload = build_missing_payload(result, os.path.abspath(out_path))
    missing_dir = os.path.dirname(os.path.abspath(missing_out_path))
    if missing_dir:
        os.makedirs(missing_dir, exist_ok=True)
    with open(missing_out_path, "w", encoding="utf-8") as f:
        json.dump(missing_payload, f, ensure_ascii=False, indent=2)
    result["_missing_out_path"] = os.path.abspath(missing_out_path)

    return result


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="按部门导出企微员工信息到 JSON")
    parser.add_argument(
        "--corp-id",
        default=os.environ.get("WECHAT_CORP_ID", ""),
        help="企业微信 corp_id（或环境变量 WECHAT_CORP_ID）",
    )
    parser.add_argument(
        "--corp-secret",
        default=os.environ.get("WECHAT_CORP_SECRET", ""),
        help="通讯录 Secret（或环境变量 WECHAT_CORP_SECRET）",
    )
    parser.add_argument(
        "--out",
        default=DEFAULT_OUT,
        help=f"输出 JSON 路径（默认 {DEFAULT_OUT}）",
    )
    parser.add_argument(
        "--missing-out",
        default=DEFAULT_MISSING_OUT,
        help=f"缺失清单 JSON 路径（默认 {DEFAULT_MISSING_OUT}）",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    if not args.corp_id or not args.corp_secret:
        print(
            "缺少凭证：请传 --corp-id / --corp-secret，"
            "或设置环境变量 WECHAT_CORP_ID / WECHAT_CORP_SECRET",
            file=sys.stderr,
        )
        return 2

    result = export_users(
        args.corp_id,
        args.corp_secret,
        args.out,
        missing_out_path=args.missing_out,
    )
    summary = result["summary"]
    print("导出完成")
    print(f"  部门数: {summary['department_count']}")
    print(f"  去重员工数: {summary['unique_user_count']}")
    print(f"  缺手机号: {summary['missing_mobile_count']}")
    print(f"  缺身份证号: {summary['missing_id_card_count']}")
    print(f"  两者都缺: {summary['missing_both_count']}")
    print(f"  输出文件: {os.path.abspath(args.out)}")
    print(f"  缺失清单: {result.get('_missing_out_path')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

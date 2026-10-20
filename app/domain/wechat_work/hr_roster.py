"""人事助手花名册快照

由 scripts/sync_hr_roster.py 手动拉取并写入 employee.hr_roster。
企微没有花名册增量接口，脚本每次都会拉当前组织的全部成员。
"""

import json
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from yweb.log import get_logger

logger = get_logger()

# 教育经历、工作经历、家庭成员、紧急联系人、合同记录
REPEATABLE_GROUP_IDS = {1004, 1005, 1006, 1007, 1008}
HR_FETCH_WORKERS = 8
_SHANGHAI = timezone(timedelta(hours=8))
_QYAPI = "https://qyapi.weixin.qq.com/cgi-bin"


def build_hr_roster(
    group_list: Sequence[dict],
    field_info: Sequence[dict],
    userid: str,
    synced_at: str,
) -> dict:
    """把字段定义和某员工的花名册结果合成一份快照。

    已配置但未返回的字段值为 null。可重复组只保留本次有返回的记录。
    """
    indexed = _index_field_info(field_info)
    groups = []
    for group in group_list:
        field_list = group.get("field_list") or []
        field_ids = {field.get("fieldid") for field in field_list}
        repeatable = group.get("group_id") in REPEATABLE_GROUP_IDS
        if repeatable:
            sub_indexes = sorted({
                sub_idx
                for (field_id, sub_idx) in indexed
                if field_id in field_ids
            })
        else:
            sub_indexes = [0]
        records = [
            {
                "sub_idx": sub_idx,
                "fields": [
                    _field_snapshot(field, indexed.get((field.get("fieldid"), sub_idx)))
                    for field in field_list
                ],
            }
            for sub_idx in sub_indexes
        ]
        groups.append({
            "group_id": group.get("group_id"),
            "group_name": group.get("group_name"),
            "repeatable": repeatable,
            "records": records,
        })
    return {
        "synced_at": synced_at,
        "userid": userid,
        "groups": groups,
    }


def apply_staff_rosters(
    employees: Iterable[Tuple[Any, str]],
    group_list: Sequence[dict],
    fetched: Dict[str, Any],
    synced_at: str,
) -> List[str]:
    """把拉取结果写入员工。失败的人不改已有快照。

    fetched 的值是 field_info 列表，或 Exception。
    """
    errors: List[str] = []
    for employee, userid in employees:
        if userid not in fetched or isinstance(fetched[userid], Exception):
            reason = fetched.get(userid, "未返回花名册")
            errors.append(f"花名册同步失败: userid={userid}: {reason}")
            continue
        payload = fetched[userid]
        employee.hr_roster = build_hr_roster(
            group_list, payload or [], userid, synced_at
        )
        employee.save(commit=True)
    return errors


def fetch_staff_field_infos(
    access_token: str,
    userids: Sequence[str],
    workers: int = HR_FETCH_WORKERS,
) -> Dict[str, Any]:
    """并发拉取花名册。返回 userid -> field_info 列表或 Exception。"""
    if not userids:
        return {}
    results: Dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        futures = {
            pool.submit(fetch_staff_field_info, access_token, userid): userid
            for userid in userids
        }
        for future in as_completed(futures):
            userid = futures[future]
            try:
                results[userid] = future.result()
            except Exception as exc:
                results[userid] = exc
    return results


def get_access_token(corp_id: str, corp_secret: str) -> str:
    query = urllib.parse.urlencode({"corpid": corp_id, "corpsecret": corp_secret})
    body = _request_json(f"{_QYAPI}/gettoken?{query}")
    token = body.get("access_token")
    if body.get("errcode") not in (0, None) or not token:
        raise ValueError(body.get("errmsg") or "获取 access_token 失败")
    return token


def get_field_groups(access_token: str) -> List[dict]:
    body = _request_json(
        f"{_QYAPI}/hr/get_fields?access_token={urllib.parse.quote(access_token)}"
    )
    if body.get("errcode") != 0:
        raise ValueError(body.get("errmsg") or "获取花名册字段失败")
    return body.get("group_list") or []


def fetch_staff_field_info(access_token: str, userid: str) -> List[dict]:
    body = _request_json(
        f"{_QYAPI}/hr/get_staff_info?access_token={urllib.parse.quote(access_token)}",
        {"userid": userid, "get_all": True},
    )
    if body.get("errcode") != 0:
        raise ValueError(body.get("errmsg") or f"获取花名册失败: {userid}")
    return body.get("field_info") or []


def now_shanghai_iso() -> str:
    return datetime.now(_SHANGHAI).isoformat(timespec="seconds")


def _request_json(url: str, body: Optional[dict] = None) -> dict:
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(
        url,
        data=data,
        method="GET" if body is None else "POST",
    )
    if body is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def _index_field_info(field_info: Sequence[dict]) -> Dict[Tuple[Any, int], dict]:
    indexed: Dict[Tuple[Any, int], dict] = {}
    for row in field_info:
        key = (row.get("fieldid"), row.get("sub_idx") or 0)
        current = indexed.get(key)
        if current is None or (current.get("result") != 1 and row.get("result") == 1):
            indexed[key] = row
    return indexed


def _field_snapshot(field: dict, row: Optional[dict]) -> dict:
    snapshot = {
        "field_id": field.get("fieldid"),
        "name": field.get("field_name"),
        "value": None,
        "option_id": None,
    }
    if row is None or row.get("result") != 1:
        if row is not None and row.get("result") in (2, 5):
            snapshot["unavailable"] = True
        return snapshot

    raw = _raw_value(row)
    if field.get("field_type") == 2:
        option_id = raw if isinstance(raw, int) else None
        snapshot["option_id"] = option_id
        snapshot["value"] = _option_text(field, option_id)
        return snapshot
    if field.get("field_type") == 3 and isinstance(raw, int):
        snapshot["value"] = _format_date(raw)
        return snapshot
    if field.get("field_type") in (4, 5, 6):
        media_ids = raw if isinstance(raw, list) else []
        snapshot["value"] = media_ids or None
        return snapshot
    if isinstance(raw, dict) and ("value_mobile" in raw or "value_country_code" in raw):
        code = str(raw.get("value_country_code") or "").strip()
        mobile = str(raw.get("value_mobile") or "").strip()
        snapshot["value"] = " ".join(part for part in (code, mobile) if part) or None
        return snapshot
    if raw in ("", [], {}):
        return snapshot
    snapshot["value"] = raw
    return snapshot


def _raw_value(row: dict) -> Any:
    value_type = row.get("value_type")
    if value_type == 1:
        return row.get("value_string")
    if value_type == 2:
        return row.get("value_uint64")
    if value_type == 3:
        return row.get("value_uint32")
    if value_type == 4:
        return row.get("value_int64")
    if value_type == 5:
        return row.get("value_mobile") or {}
    if value_type == 6:
        return (row.get("value_file") or {}).get("media_id") or []
    return None


def _option_text(field: dict, option_id: Optional[int]) -> Optional[str]:
    if option_id is None:
        return None
    for option in field.get("option_list") or []:
        if option.get("id") == option_id:
            return option.get("value")
    return str(option_id)


def _format_date(raw: int) -> str:
    timestamp = raw / 1000 if raw > 10**12 else raw
    try:
        return datetime.fromtimestamp(timestamp, _SHANGHAI).strftime("%Y-%m-%d")
    except (OverflowError, OSError, ValueError):
        return str(raw)

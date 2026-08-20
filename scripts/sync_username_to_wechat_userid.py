#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 User.username 更新为关联员工的 enterprise_wechat_user_id。

读取当前部署目录下的 config/settings.yaml，因此拷到其他环境后直接执行即可。

只处理「已关联员工且员工有企微 userid」的账号；无员工、无 userid 的用户会跳过。
目标用户名已被其他人占用时跳过，不覆盖。

用法（在项目根目录或任意目录均可）:
  python scripts/sync_username_to_wechat_userid.py --dry-run
  python scripts/sync_username_to_wechat_userid.py
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import app.database  # noqa: F401
from yweb.log import get_logger

from app.config import settings
from app.domain.auth.model.user import User
from app.models_registry import ensure_dynamic_models

logger = get_logger()

# AbstractUser.username 列长 50
USERNAME_MAX_LEN = 50
TEMP_PREFIX = "_tmpu_"


def mask_db_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.password:
        return url
    host = parsed.hostname or ""
    if parsed.port:
        host = f"{host}:{parsed.port}"
    netloc = f"{parsed.username}:***@{host}"
    return urlunparse(parsed._replace(netloc=netloc))


def normalize_wechat_user_id(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def collect_updates(employee_model) -> Tuple[List[dict], Dict[str, int]]:
    """收集需要改名的用户。返回 (计划列表, 统计)。"""
    stats = {
        "users_total": 0,
        "already_ok": 0,
        "skipped_no_employee": 0,
        "skipped_no_wechat_id": 0,
        "skipped_too_long": 0,
        "skipped_conflict": 0,
        "planned": 0,
    }

    emp_by_user_id: Dict[int, Any] = {}
    employees = employee_model.query.filter(
        employee_model.user_id.isnot(None),
    ).all()
    for emp in employees:
        user_id = emp.user_id
        existing = emp_by_user_id.get(user_id)
        if existing is None:
            emp_by_user_id[user_id] = emp
            continue
        if not normalize_wechat_user_id(
            existing.enterprise_wechat_user_id
        ) and normalize_wechat_user_id(emp.enterprise_wechat_user_id):
            emp_by_user_id[user_id] = emp

    users = User.query.all()
    stats["users_total"] = len(users)

    candidates: List[dict] = []
    target_owners: Dict[str, int] = {}

    for user in users:
        emp = emp_by_user_id.get(user.id)
        if emp is None:
            stats["skipped_no_employee"] += 1
            continue

        wechat_user_id = normalize_wechat_user_id(emp.enterprise_wechat_user_id)
        if not wechat_user_id:
            stats["skipped_no_wechat_id"] += 1
            print(
                f"跳过(无企微userid): user_id={user.id} username={user.username} "
                f"emp_id={emp.id} name={emp.name}"
            )
            continue

        if len(wechat_user_id) > USERNAME_MAX_LEN:
            stats["skipped_too_long"] += 1
            print(
                f"跳过(userid超长>{USERNAME_MAX_LEN}): user_id={user.id} "
                f"username={user.username} wechat_user_id={wechat_user_id}"
            )
            continue

        if user.username == wechat_user_id:
            stats["already_ok"] += 1
            continue

        owner = target_owners.get(wechat_user_id)
        if owner is not None:
            stats["skipped_conflict"] += 1
            print(
                f"跳过(多个员工同一userid): user_id={user.id} username={user.username} "
                f"wechat_user_id={wechat_user_id} 已占用计划 user_id={owner}"
            )
            continue
        target_owners[wechat_user_id] = user.id

        candidates.append(
            {
                "user": user,
                "old": user.username,
                "new": wechat_user_id,
                "emp_id": emp.id,
                "emp_name": emp.name,
            }
        )

    planned: List[dict] = []
    changing_ids = {item["user"].id for item in candidates}

    for item in candidates:
        holder = User.get_by_username(item["new"])
        if holder and holder.id != item["user"].id and holder.id not in changing_ids:
            stats["skipped_conflict"] += 1
            print(
                f"跳过(用户名已被占用): user_id={item['user'].id} "
                f"{item['old']} -> {item['new']} 占用者 user_id={holder.id}"
            )
            continue
        planned.append(item)

    stats["planned"] = len(planned)
    return planned, stats


def apply_updates(planned: List[dict], dry_run: bool) -> int:
    """先改临时名再落到企微 userid，避免互相占用。"""

    def _rename(user, new_name: str, extra: str) -> None:
        prefix = "[dry-run] " if dry_run else ""
        line = f"{prefix}{extra}: user_id={user.id} {user.username} -> {new_name}"
        logger.info(line)
        print(line)
        if not dry_run:
            user.username = new_name
            user.save(commit=True)

    current_names = {item["old"]: item for item in planned}
    holders_to_park = []
    seen_ids = set()
    for item in planned:
        holder_item = current_names.get(item["new"])
        if (
            holder_item is not None
            and holder_item["user"].id != item["user"].id
            and holder_item["user"].id not in seen_ids
        ):
            holders_to_park.append(holder_item)
            seen_ids.add(holder_item["user"].id)

    for item in holders_to_park:
        _rename(item["user"], f"{TEMP_PREFIX}{item['user'].id}", "临时改名")

    for item in planned:
        _rename(
            item["user"],
            item["new"],
            f"同步 username emp_id={item['emp_id']} name={item['emp_name']}",
        )

    return len(planned)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="将 User.username 同步为 Employee.enterprise_wechat_user_id"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要更新的记录，不写库",
    )
    args = parser.parse_args()

    db_url = getattr(settings.database, "url", "")
    print(f"数据库: {mask_db_url(db_url)}")
    print(f"配置文件: {os.path.join(ROOT, 'config', 'settings.yaml')}")
    if args.dry_run:
        print("模式: dry-run（不写库）")

    registry = ensure_dynamic_models()
    employee_model = registry.org_models.Employee

    planned, stats = collect_updates(employee_model)
    updated = apply_updates(planned, dry_run=args.dry_run) if planned else 0

    summary = (
        f"完成{'（dry-run）' if args.dry_run else ''}："
        f"用户 {stats['users_total']}，"
        f"已是企微userid {stats['already_ok']}，"
        f"更新 {updated}，"
        f"无员工 {stats['skipped_no_employee']}，"
        f"无userid {stats['skipped_no_wechat_id']}，"
        f"超长 {stats['skipped_too_long']}，"
        f"冲突 {stats['skipped_conflict']}"
    )
    logger.info(summary)
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

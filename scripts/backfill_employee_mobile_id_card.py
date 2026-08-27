#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""回填员工表缺失的手机号 / 身份证号（从企微 user/list 拉取）。

仅更新本地为空、企微有值的字段；不会覆盖已有值。

用法:
  python scripts/backfill_employee_mobile_id_card.py
  python scripts/backfill_employee_mobile_id_card.py --org-id 1
  python scripts/backfill_employee_mobile_id_card.py --dry-run
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

# 初始化数据库与动态模型
import app.database  # noqa: F401
from yweb.log import get_logger
from yweb.organization import ExternalSource

from app.domain.wechat_work import WechatWorkClient
from app.domain.wechat_work.attrs import extract_id_card, normalize_mobile
from app.models_registry import ensure_dynamic_models

logger = get_logger()

WECHAT_ROOT_DEPT_ID = "1"


def fetch_wechat_users(client: WechatWorkClient) -> Dict[str, Dict[str, Any]]:
    """按部门拉取企微成员详情，按 userid 去重。"""
    raw_depts = client.get_departments()
    dept_ids = [WECHAT_ROOT_DEPT_ID]
    for d in raw_depts:
        dept_id = str(d.get("id", ""))
        if dept_id and dept_id != WECHAT_ROOT_DEPT_ID:
            dept_ids.append(dept_id)

    users: Dict[str, Dict[str, Any]] = {}
    for dept_id in dept_ids:
        try:
            members = client.get_department_users(int(dept_id))
        except ValueError as e:
            logger.warning(f"跳过部门 {dept_id}: {e}")
            continue
        for u in members:
            uid = str(u.get("userid") or "").strip()
            if not uid:
                continue
            if uid not in users:
                users[uid] = u
            else:
                # 合并时补全敏感字段
                if not normalize_mobile(users[uid]) and normalize_mobile(u):
                    users[uid] = u
                elif not extract_id_card(users[uid]) and extract_id_card(u):
                    users[uid] = u
    return users


def list_wechat_orgs(org_model, org_id: Optional[int] = None) -> List[Any]:
    query = org_model.query.filter(
        org_model.external_source == ExternalSource.WECHAT_WORK.value,
    )
    if org_id is not None:
        query = query.filter(org_model.id == org_id)
    return query.all()


def backfill_org(
    org,
    employee_model,
    emp_org_rel_model,
    dry_run: bool = False,
) -> Tuple[int, int, int]:
    """回填单个组织。返回 (检查人数, 更新手机号数, 更新身份证数)。"""
    client = WechatWorkClient.from_organization(org)
    remote_users = fetch_wechat_users(client)
    logger.info(f"组织 [{org.name}] 企微成员 {len(remote_users)} 人")

    rels = emp_org_rel_model.query.filter(
        emp_org_rel_model.org_id == org.id,
        emp_org_rel_model.external_user_id.isnot(None),
    ).all()

    checked = 0
    mobile_updated = 0
    id_card_updated = 0

    for rel in rels:
        userid = (rel.external_user_id or "").strip()
        if not userid:
            continue

        emp = employee_model.get(rel.employee_id)
        if not emp:
            continue

        checked += 1
        remote = remote_users.get(userid)

        # 优先用企微详情；远端已删/离职时，再从本地姓名等字段抠手机号
        remote_mobile = normalize_mobile(remote) if remote else None
        local_mobile = normalize_mobile({"name": emp.name or ""})
        remote_id_card = extract_id_card(remote) if remote else None

        changed = False
        if not (emp.mobile or "").strip():
            mobile = remote_mobile or local_mobile
            if mobile:
                source = "企微" if remote_mobile else "本地姓名"
                logger.info(
                    f"{'[dry-run] ' if dry_run else ''}"
                    f"补手机号({source}): emp_id={emp.id} userid={userid} "
                    f"name={emp.name} -> {mobile}"
                )
                print(
                    f"{'[dry-run] ' if dry_run else ''}"
                    f"补手机号({source}): emp_id={emp.id} userid={userid} "
                    f"name={emp.name} -> {mobile}"
                )
                if not dry_run:
                    emp.mobile = mobile
                mobile_updated += 1
                changed = True

        if remote_id_card and not (emp.id_card or "").strip():
            logger.info(
                f"{'[dry-run] ' if dry_run else ''}"
                f"补身份证号: emp_id={emp.id} userid={userid} name={emp.name}"
            )
            if not dry_run:
                emp.id_card = remote_id_card
            id_card_updated += 1
            changed = True

        if changed and not dry_run:
            emp.save(commit=True)

    return checked, mobile_updated, id_card_updated


def main() -> int:
    parser = argparse.ArgumentParser(description="回填员工手机号/身份证号")
    parser.add_argument("--org-id", type=int, default=None, help="仅处理指定组织 ID")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要更新的记录，不写库",
    )
    args = parser.parse_args()

    registry = ensure_dynamic_models()
    org_model = registry.org_models.Organization
    employee_model = registry.org_models.Employee
    emp_org_rel_model = registry.org_models.EmployeeOrgRel

    orgs = list_wechat_orgs(org_model, args.org_id)
    if not orgs:
        logger.error("未找到已绑定企业微信的组织")
        return 1

    total_checked = total_mobile = total_id_card = 0
    for org in orgs:
        logger.info(f"开始回填组织: id={org.id} name={org.name}")
        try:
            checked, mobile_n, id_card_n = backfill_org(
                org,
                employee_model,
                emp_org_rel_model,
                dry_run=args.dry_run,
            )
        except ValueError as e:
            logger.error(f"组织 [{org.name}] 回填失败: {e}")
            continue
        total_checked += checked
        total_mobile += mobile_n
        total_id_card += id_card_n
        logger.info(
            f"组织 [{org.name}] 完成: 匹配 {checked}，"
            f"补手机号 {mobile_n}，补身份证号 {id_card_n}"
        )

    logger.info(
        f"全部完成{'（dry-run）' if args.dry_run else ''}："
        f"匹配 {total_checked}，补手机号 {total_mobile}，补身份证号 {total_id_card}"
    )
    print(
        f"全部完成{'（dry-run）' if args.dry_run else ''}："
        f"匹配 {total_checked}，补手机号 {total_mobile}，补身份证号 {total_id_card}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

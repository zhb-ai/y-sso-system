#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从企业微信全量同步组织架构和通讯录。

等同于管理接口 POST /api/v1/wechat-work/sync/manual。
直接调用同步服务，不走 HTTP，因此不需要管理员 Token。
适合在生产机用 cron 或计划任务定时执行。

不拉取花名册。花名册仍用 scripts/sync_hr_roster.py。

用法:
  python scripts/sync_wechat_work_contacts.py
  python scripts/sync_wechat_work_contacts.py --org-id 1
"""
from __future__ import annotations

import argparse
import os
import sys
from typing import List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

import app.database  # noqa: F401
from yweb.log import get_logger
from yweb.organization import ExternalSource

from app.domain.wechat_work import WechatWorkClient, WechatWorkSyncService
from app.models_registry import ensure_dynamic_models

logger = get_logger()


def list_wechat_orgs(org_model, org_id: Optional[int] = None) -> List:
    query = org_model.query.filter(
        org_model.external_source == ExternalSource.WECHAT_WORK.value,
    )
    if org_id is not None:
        query = query.filter(org_model.id == org_id)
    return query.all()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="从企业微信全量同步组织架构和通讯录",
    )
    parser.add_argument("--org-id", type=int, default=None, help="仅同步指定组织 ID")
    args = parser.parse_args()

    registry = ensure_dynamic_models()
    orgs = list_wechat_orgs(registry.org_models.Organization, args.org_id)
    if not orgs:
        print("未找到已绑定企业微信的组织")
        return 1

    failed = False
    for org in orgs:
        print(f"开始同步通讯录: id={org.id} name={org.name}")
        try:
            client = WechatWorkClient.from_organization(org)
            service = WechatWorkSyncService(client, registry.org_models)
            result = service.sync_from_external(org.id)
        except Exception as exc:
            print(f"组织 [{org.name}] 通讯录同步失败: {exc}")
            logger.exception("通讯录同步失败: org_id=%s", org.id)
            failed = True
            continue

        errors = list(result.errors or [])
        summary = (
            f"新建={result.created_count}, 更新={result.updated_count}, "
            f"删除={result.deleted_count}, 耗时={result.duration_seconds:.1f}s"
        )
        if errors or not result.success:
            failed = True
            print(f"组织 [{org.name}] 完成，失败 {len(errors)} 条: {summary}")
            for error in errors:
                print(error)
        else:
            print(f"组织 [{org.name}] 完成: {summary}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

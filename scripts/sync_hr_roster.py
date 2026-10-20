#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动拉取企业微信花名册，写入 employee.hr_roster。

通讯录同步不会执行这一步。需要花名册时再运行本脚本。
每次都会拉取该组织全部有企微 userid 的员工，单人失败不会覆盖已有快照。

用法:
  python scripts/sync_hr_roster.py
  python scripts/sync_hr_roster.py --org-id 1
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
    parser = argparse.ArgumentParser(description="拉取花名册并写入 employee.hr_roster")
    parser.add_argument("--org-id", type=int, default=None, help="仅处理指定组织 ID")
    args = parser.parse_args()

    registry = ensure_dynamic_models()
    orgs = list_wechat_orgs(registry.org_models.Organization, args.org_id)
    if not orgs:
        print("未找到已绑定企业微信的组织")
        return 1

    failed = False
    for org in orgs:
        print(f"开始拉取花名册: id={org.id} name={org.name}")
        try:
            client = WechatWorkClient.from_organization(org)
            service = WechatWorkSyncService(client, registry.org_models)
            errors = service.sync_hr_roster(org.id)
        except Exception as exc:
            print(f"组织 [{org.name}] 花名册拉取失败: {exc}")
            failed = True
            continue
        if errors:
            failed = True
            print(f"组织 [{org.name}] 完成，失败 {len(errors)} 人")
            for error in errors:
                print(error)
        else:
            print(f"组织 [{org.name}] 完成")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

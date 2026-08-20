#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从远程 SSO 用户列表 + 部门树 JSON，导入到本地数据库。

用法:
  python scripts/import_remote_org_users.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.chdir(ROOT)

from yweb.auth import PasswordHelper
from yweb.log import get_logger
from yweb.orm import BaseModel, db_manager

from app.database import get_engine
from app.models_registry import User, ensure_dynamic_models

logger = get_logger()

USERS_JSON = os.path.join(ROOT, "users_list_response.json")
DEPTS_JSON = os.path.join(ROOT, "departments_tree.json")

DEFAULT_PASSWORD = "ChangeMe@123"
ADMIN_PASSWORD = "admin123"


def ensure_tables_and_roles(registry) -> None:
    BaseModel.metadata.create_all(bind=get_engine())
    Role = registry.role_model
    db = db_manager.get_session()
    try:
        for code, name, desc in (
            ("admin", "管理员", "系统管理员，拥有所有权限"),
            ("user", "内部员工", "内部员工，拥有业务相关权限"),
            ("external", "外部用户", "外部用户，拥有受限权限"),
        ):
            role = db.query(Role).filter(Role.code == code).first()
            if not role:
                role = Role(name=name, code=code, description=desc)
                db.add(role)
                db.flush()
                logger.info(f"创建角色: {code}")
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def flatten_depts(nodes: List[dict], acc: Optional[List[dict]] = None) -> List[dict]:
    if acc is None:
        acc = []
    for node in nodes:
        item = {k: v for k, v in node.items() if k != "children"}
        acc.append(item)
        children = node.get("children") or []
        if children:
            flatten_depts(children, acc)
    return acc


def parse_created_at(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def reset_seq(db, table: str) -> None:
    db.execute(
        text(
            "SELECT setval("
            f"pg_get_serial_sequence('\"{table}\"', 'id'), "
            f"COALESCE((SELECT MAX(id) FROM \"{table}\"), 1), true)"
        )
    )


def import_organization(db) -> int:
    """确保 organization.id=1 存在，返回 org_id。"""
    row = db.execute(
        text('SELECT id, name FROM organization WHERE id = 1 AND deleted_at IS NULL')
    ).first()
    if row:
        logger.info(f"组织已存在: id={row[0]} name={row[1]}")
        return 1

    db.execute(
        text(
            """
            INSERT INTO organization
                (id, name, code, is_active, external_source, ver, created_at)
            VALUES
                (1, :name, :code, true, 'none', 1, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                code = EXCLUDED.code,
                is_active = true,
                deleted_at = NULL
            """
        ),
        {"name": "好采", "code": "haocai"},
    )
    logger.info("创建组织: id=1 name=好采")
    return 1


def import_departments(db, flat: List[dict], org_id: int) -> Tuple[int, int]:
    """先插节点（无 parent），再挂 parent，最后刷 path/level。"""
    by_id = {item["id"]: item for item in flat}
    created = 0
    updated = 0

    for item in flat:
        dept_id = item["id"]
        exists = db.execute(
            text("SELECT id FROM department WHERE id = :id"),
            {"id": dept_id},
        ).first()

        params = {
            "id": dept_id,
            "org_id": org_id,
            "name": item["name"],
            "code": item.get("code"),
            "caption": item.get("caption"),
            "sort_order": item.get("sort_order") or 0,
            "external_dept_id": (
                str(item["external_dept_id"])
                if item.get("external_dept_id") is not None
                else None
            ),
            "external_parent_id": (
                str(item["external_parent_id"])
                if item.get("external_parent_id") is not None
                else None
            ),
            "is_active": bool(item.get("is_active", True)),
        }

        if exists:
            db.execute(
                text(
                    """
                    UPDATE department SET
                        org_id = :org_id,
                        name = :name,
                        code = :code,
                        caption = :caption,
                        parent_id = NULL,
                        level = 1,
                        path = NULL,
                        sort_order = :sort_order,
                        external_dept_id = :external_dept_id,
                        external_parent_id = :external_parent_id,
                        is_active = :is_active,
                        deleted_at = NULL,
                        updated_at = NOW(),
                        ver = ver + 1
                    WHERE id = :id
                    """
                ),
                params,
            )
            updated += 1
        else:
            db.execute(
                text(
                    """
                    INSERT INTO department
                        (id, org_id, name, code, caption, parent_id, level, path,
                         sort_order, external_dept_id, external_parent_id,
                         is_active, ver, created_at)
                    VALUES
                        (:id, :org_id, :name, :code, :caption, NULL, 1, NULL,
                         :sort_order, :external_dept_id, :external_parent_id,
                         :is_active, 1, NOW())
                    """
                ),
                params,
            )
            created += 1

    db.flush()

    # 挂 parent
    for item in flat:
        parent_id = item.get("parent_id")
        if parent_id is not None and parent_id not in by_id:
            parent_id = None
        db.execute(
            text("UPDATE department SET parent_id = :pid WHERE id = :id"),
            {"pid": parent_id, "id": item["id"]},
        )

    db.flush()

    # 拓扑序计算 path/level
    remaining = set(by_id.keys())
    ordered: List[int] = []
    while remaining:
        progress = False
        for dept_id in list(remaining):
            parent_id = by_id[dept_id].get("parent_id")
            if parent_id is None or parent_id not in by_id or parent_id in ordered:
                ordered.append(dept_id)
                remaining.remove(dept_id)
                progress = True
        if not progress:
            ordered.extend(sorted(remaining))
            break

    path_map: Dict[int, str] = {}
    level_map: Dict[int, int] = {}
    for dept_id in ordered:
        parent_id = by_id[dept_id].get("parent_id")
        if parent_id is None or parent_id not in by_id:
            level = 1
            path = f"/{dept_id}/"
        else:
            level = level_map[parent_id] + 1
            path = f"{path_map[parent_id]}{dept_id}/"
        path_map[dept_id] = path
        level_map[dept_id] = level
        db.execute(
            text(
                "UPDATE department SET path = :path, level = :level WHERE id = :id"
            ),
            {"path": path, "level": level, "id": dept_id},
        )

    return created, updated


def import_users(db, Role, rows: List[dict]) -> Tuple[int, int]:
    created = 0
    updated = 0
    role_map = {r.code: r for r in db.query(Role).all()}

    for row in rows:
        remote_id = row["id"]
        username = row["username"]
        existing = (
            db.query(User).filter(User.id == remote_id).first()
            or db.query(User).filter(User.username == username).first()
        )

        is_active = (row.get("status") or "active") == "active"
        name = row.get("name")
        email = row.get("email")
        phone = row.get("phone")
        created_at = parse_created_at(row.get("created_at"))
        role_codes = [r.get("code") for r in (row.get("roles") or []) if r.get("code")]
        if not role_codes:
            role_codes = ["user"]

        if existing:
            existing.name = name
            existing.email = email
            existing.phone = phone
            existing.is_active = is_active
            existing.roles.clear()
            for code in role_codes:
                role = role_map.get(code)
                if role is not None:
                    existing.roles.append(role)
            updated += 1
        else:
            pwd = ADMIN_PASSWORD if username == "admin" else DEFAULT_PASSWORD
            # 用原生 SQL 写入显式 id，避免自增列吞掉 id
            db.execute(
                text(
                    """
                    INSERT INTO "user"
                        (id, username, password_hash, email, phone, name,
                         is_active, is_locked, failed_login_attempts,
                         must_change_password, ver, created_at)
                    VALUES
                        (:id, :username, :password_hash, :email, :phone, :name,
                         :is_active, false, 0,
                         :must_change_password, 1, COALESCE(:created_at, NOW()))
                    """
                ),
                {
                    "id": remote_id,
                    "username": username,
                    "password_hash": PasswordHelper.hash(pwd),
                    "email": email,
                    "phone": phone,
                    "name": name,
                    "is_active": is_active,
                    "must_change_password": username != "admin",
                    "created_at": created_at,
                },
            )
            db.flush()
            user = db.query(User).filter(User.id == remote_id).one()
            for code in role_codes:
                role = role_map.get(code)
                if role is not None:
                    user.roles.append(role)
            created += 1

        db.flush()

    return created, updated


def main():
    if not os.path.exists(USERS_JSON):
        raise SystemExit(f"缺少用户数据文件: {USERS_JSON}")
    if not os.path.exists(DEPTS_JSON):
        raise SystemExit(f"缺少部门数据文件: {DEPTS_JSON}")

    with open(USERS_JSON, encoding="utf-8") as f:
        users_payload = json.load(f)
    with open(DEPTS_JSON, encoding="utf-8") as f:
        depts_payload = json.load(f)

    user_rows = users_payload["data"]["rows"]
    dept_tree = (
        depts_payload["data"]
        if isinstance(depts_payload.get("data"), list)
        else depts_payload
    )
    flat_depts = flatten_depts(dept_tree)

    registry = ensure_dynamic_models()
    Role = registry.role_model
    org_models = registry.org_models

    ensure_tables_and_roles(registry)

    db = db_manager.get_session()
    try:
        org_id = import_organization(db)
        db.flush()

        c, u = import_departments(db, flat_depts, org_id)
        logger.info(f"部门导入完成: created={c}, updated={u}, total={len(flat_depts)}")

        c, u = import_users(db, Role, user_rows)
        logger.info(f"用户导入完成: created={c}, updated={u}, total={len(user_rows)}")

        for table in ("user", "organization", "department", "role"):
            try:
                reset_seq(db, table)
            except Exception as e:
                logger.warning(f"重置序列失败 {table}: {e}")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        # 汇总前再开
        pass

    print("==== 导入结果 ====")
    print(f"organization: {db.query(org_models.Organization).count()}")
    print(f"department:   {db.query(org_models.Department).count()}")
    print(f"user:         {db.query(User).count()}")
    print(f"role:         {db.query(Role).count()}")
    print(f"默认密码(非admin): {DEFAULT_PASSWORD}")
    print(f"admin 密码: {ADMIN_PASSWORD}")
    db.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""将 SQLite 中的 application 表数据导入到当前 PostgreSQL。"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from yweb.orm import BaseModel, db_manager

from app.database import get_engine
from app.models_registry import ensure_dynamic_models

SQLITE_PATH = ROOT / "app" / "db" / "y_sso.db"


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    for fmt in (
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def load_sqlite_apps() -> list[Dict[str, Any]]:
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM application ORDER BY id")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def main():
    if not SQLITE_PATH.exists():
        raise SystemExit(f"SQLite 不存在: {SQLITE_PATH}")

    ensure_dynamic_models()
    BaseModel.metadata.create_all(bind=get_engine())

    rows = load_sqlite_apps()
    print(f"SQLite application 行数: {len(rows)}")

    db = db_manager.get_session()
    created = updated = 0
    try:
        for row in rows:
            app_id = row["id"]
            exists = db.execute(
                text("SELECT id FROM application WHERE id = :id"),
                {"id": app_id},
            ).first()

            params = {
                "id": app_id,
                "name": row["name"],
                "code": row["code"],
                "description": row.get("description"),
                "client_id": row["client_id"],
                "client_secret": row.get("client_secret") or "",
                "client_type": row.get("client_type") or "confidential",
                "redirect_uris": row.get("redirect_uris"),
                "allowed_ip_cidrs": row.get("allowed_ip_cidrs"),
                "logo_url": row.get("logo_url"),
                "is_active": bool(row.get("is_active", True)),
                "note": row.get("note"),
                "caption": row.get("caption"),
                "ver": row.get("ver") or 1,
                "created_at": parse_dt(row.get("created_at")),
                "updated_at": parse_dt(row.get("updated_at")),
                "deleted_at": parse_dt(row.get("deleted_at")),
            }

            if exists:
                db.execute(
                    text(
                        """
                        UPDATE application SET
                            name = :name,
                            code = :code,
                            description = :description,
                            client_id = :client_id,
                            client_secret = :client_secret,
                            client_type = :client_type,
                            redirect_uris = :redirect_uris,
                            allowed_ip_cidrs = :allowed_ip_cidrs,
                            logo_url = :logo_url,
                            is_active = :is_active,
                            note = :note,
                            caption = :caption,
                            ver = :ver,
                            created_at = COALESCE(:created_at, created_at),
                            updated_at = :updated_at,
                            deleted_at = :deleted_at
                        WHERE id = :id
                        """
                    ),
                    params,
                )
                updated += 1
                print(f"UPDATE id={app_id} code={row['code']} name={row['name']}")
            else:
                db.execute(
                    text(
                        """
                        INSERT INTO application
                            (id, name, code, description, client_id, client_secret,
                             client_type, redirect_uris, allowed_ip_cidrs, logo_url,
                             is_active, note, caption, ver, created_at, updated_at, deleted_at)
                        VALUES
                            (:id, :name, :code, :description, :client_id, :client_secret,
                             :client_type, :redirect_uris, :allowed_ip_cidrs, :logo_url,
                             :is_active, :note, :caption, :ver,
                             COALESCE(:created_at, NOW()), :updated_at, :deleted_at)
                        """
                    ),
                    params,
                )
                created += 1
                print(f"INSERT id={app_id} code={row['code']} name={row['name']}")

        db.execute(
            text(
                "SELECT setval("
                "pg_get_serial_sequence('application', 'id'), "
                "COALESCE((SELECT MAX(id) FROM application), 1), true)"
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    total = db.execute(text("SELECT COUNT(*) FROM application")).scalar()
    active = db.execute(
        text("SELECT COUNT(*) FROM application WHERE deleted_at IS NULL")
    ).scalar()
    print("==== 导入结果 ====")
    print(f"created={created}, updated={updated}")
    print(f"pg application total={total}, active(未软删)={active}")
    for r in db.execute(
        text(
            "SELECT id, code, name, client_type, is_active, "
            "(deleted_at IS NOT NULL) AS soft_deleted, client_id "
            "FROM application ORDER BY id"
        )
    ):
        print(
            f"  id={r[0]} code={r[1]} name={r[2]} type={r[3]} "
            f"active={r[4]} deleted={r[5]} client_id={r[6][:16]}..."
        )
    db.close()


if __name__ == "__main__":
    main()

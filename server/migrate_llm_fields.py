# -*- coding: utf-8 -*-
"""迁移脚本：给 users 表添加 LLM 配置新字段"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "test.db")


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 检查字段是否已存在
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]

    new_fields = [
        ("llm_notes", "VARCHAR(200)"),
        ("llm_website", "VARCHAR(500)"),
        ("llm_api_key_url", "VARCHAR(500)"),
    ]

    for col_name, col_type in new_fields:
        if col_name not in columns:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"[OK] Added column: {col_name}")
        else:
            print(f"[SKIP] Column already exists: {col_name}")

    conn.commit()
    conn.close()
    print("[DONE] Migration complete")


if __name__ == "__main__":
    migrate()

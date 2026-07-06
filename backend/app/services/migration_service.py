from sqlalchemy import Engine, inspect, text


# 当前项目使用轻量 SQLite 部署；这里采用幂等字段迁移，保留已有演示数据。
SCHEMA_COLUMNS = {
    "weekly_reports": {
        "push_status": "VARCHAR(30) NOT NULL DEFAULT 'not_pushed'",
    },
    "agent_runs": {
        "output_count": "INTEGER NOT NULL DEFAULT 0",
        "duration_ms": "INTEGER NOT NULL DEFAULT 0",
    },
}


def migrate_schema(engine: Engine) -> None:
    """为已有数据库补充字段；重复启动不会重复执行迁移。"""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.begin() as connection:
        for table_name, columns in SCHEMA_COLUMNS.items():
            if table_name not in existing_tables:
                continue
            existing_columns = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing_columns:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}"))

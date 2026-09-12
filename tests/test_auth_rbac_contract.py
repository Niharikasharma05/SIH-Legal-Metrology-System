import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_sync_db_layer_is_not_changed_to_async():
    source = (ROOT / "db.py").read_text(encoding="utf-8")
    assert "create_engine" in source
    assert "create_async_engine" not in source


def test_async_auth_and_rbac_are_present():
    assert "create_async_engine" in (ROOT / "auth_db.py").read_text(encoding="utf-8")
    source = (ROOT / "auth.py").read_text(encoding="utf-8")
    assert "current_active_officer" in source
    assert "current_active_admin" in source


def test_migration_creates_users_before_scan_ownership():
    source = (ROOT / "migrations" / "versions" / "0002_users_and_scan_ownership.py").read_text(encoding="utf-8")
    assert source.index('"users"') < source.index('op.add_column("scans"')
    assert "scanned_by_id" in source


def test_cors_is_restricted_and_scan_routes_require_officer():
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "allow_origins=settings.allowed_cors_origins" in source
    assert 'allow_origins=["*"]' not in source
    assert source.count("Depends(current_active_officer)") == 4
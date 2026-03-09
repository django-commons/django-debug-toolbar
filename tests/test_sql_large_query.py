import pytest

from debug_toolbar.panels.sql.utils import reformat_sql


def test_reformat_sql_with_huge_in_clause():
    """Test that huge IN clauses don't cause crashes"""
    # Create a SQL with a huge IN clause (5000 items)
    items = [f"'{i}'" for i in range(5000)]
    sql = f"SELECT * FROM table WHERE id IN ({','.join(items)})"

    # This should not raise an exception
    try:
        result = reformat_sql(sql, with_toggle=False)
        assert isinstance(result, str)
        assert len(result) > 0
    except Exception as e:
        pytest.fail(f"reformat_sql raised {type(e).__name__}: {e}")


def test_reformat_sql_with_toggle_and_huge_in_clause():
    """Test with_toggle=True with huge IN clause"""
    items = [f"'{i}'" for i in range(5000)]
    sql = f"SELECT * FROM table WHERE id IN ({','.join(items)})"

    try:
        result = reformat_sql(sql, with_toggle=True)
        assert isinstance(result, str)
        assert "djDebugUncollapsed" in result
        assert "djDebugCollapsed" in result
    except Exception as e:
        pytest.fail(f"reformat_sql (with_toggle) raised {type(e).__name__}: {e}")


def test_reformat_sql_with_invalid_sql():
    """Test that invalid SQL is handled gracefully"""
    sql = "SELECT * FROM WHERE"  # Invalid SQL

    result = reformat_sql(sql, with_toggle=False)
    assert isinstance(result, str)
    # Should either contain the SQL or an error message
    assert len(result) > 0

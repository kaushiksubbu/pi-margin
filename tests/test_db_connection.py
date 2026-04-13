from src.common_func.db_utils import connect_to_db_readonly
from src.common_func.config import BRONZE_DB

def test_sentinel_db_connection():
    """Verify we can reach the shared bronze DB."""
    try:
        con = connect_to_db_readonly(BRONZE_DB)
        # Check if we can see the Sentinel tables
        result = con.execute("SELECT 1").fetchone()
        assert result[0] == 1
        con.close()
    except Exception as e:
        pytest.fail(f"Database connection failed: {e}")pip install pytest pytest-mock
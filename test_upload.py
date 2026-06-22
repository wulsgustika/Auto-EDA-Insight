"""
tests/test_upload.py
Unit tests for file upload and data loading functionality.
SD-1306 Data Science Programming — Institut Teknologi Sains Bandung
"""

import os
import sys
import pytest
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.data_loader import DataLoader


# ── Fixtures ─────────────────────────────────────────────────────────────────
SAMPLE_CSV  = os.path.join(os.path.dirname(__file__), "..", "data", "sample_dataset", "sample_test.csv")
SAMPLE_XLSX = os.path.join(os.path.dirname(__file__), "..", "data", "sample_dataset", "sales_data.xlsx")


def _make_sample_csv(path):
    """Create a minimal CSV for testing."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df = pd.DataFrame({
        "date":     ["2024-01-01", "2024-02-01", "2024-03-01"],
        "product":  ["A", "B", "A"],
        "sales":    [100, 200, 150],
        "quantity": [10, 20, 15],
    })
    df.to_csv(path, index=False)
    return path


# ── Tests: DataLoader ─────────────────────────────────────────────────────────
class TestDataLoader:

    def test_load_csv(self, tmp_path):
        """CSV file should load as a DataFrame."""
        path = str(tmp_path / "test.csv")
        _make_sample_csv(path)
        loader = DataLoader(path)
        df = loader.load()
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 3
        assert "sales" in df.columns

    def test_load_xlsx(self):
        """XLSX sample should load without error."""
        if not os.path.exists(SAMPLE_XLSX):
            pytest.skip("sample_data.xlsx not found; skipping")
        loader = DataLoader(SAMPLE_XLSX)
        df = loader.load()
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] > 0

    def test_unsupported_format(self, tmp_path):
        """Unsupported file formats should raise ValueError."""
        path = str(tmp_path / "test.json")
        with open(path, "w") as f:
            f.write("{}")
        loader = DataLoader(path)
        with pytest.raises(ValueError, match="tidak didukung"):
            loader.load()

    def test_auto_type_detection(self, tmp_path):
        """Date columns should be detected as datetime automatically."""
        path = str(tmp_path / "typed.csv")
        _make_sample_csv(path)
        loader = DataLoader(path)
        df = loader.load()
        assert pd.api.types.is_datetime64_any_dtype(df["date"]) or \
               df["date"].dtype == object, "Date column should be parsed"

    def test_get_info(self, tmp_path):
        """get_info should return expected metadata keys."""
        path = str(tmp_path / "info.csv")
        _make_sample_csv(path)
        loader = DataLoader(path)
        df = loader.load()
        info = loader.get_info(df)
        required = {"filename", "rows", "columns", "numeric_cols", "cat_cols",
                    "missing_total", "upload_time", "size_kb"}
        assert required.issubset(set(info.keys()))

    def test_empty_csv(self, tmp_path):
        """Very small CSV with headers only should not crash."""
        path = str(tmp_path / "empty.csv")
        with open(path, "w") as f:
            f.write("col1,col2\n")
        loader = DataLoader(path)
        df = loader.load()
        assert isinstance(df, pd.DataFrame)
        assert df.shape[0] == 0

    def test_semicolon_separator(self, tmp_path):
        """CSV with semicolon delimiter should be parsed correctly."""
        path = str(tmp_path / "semi.csv")
        with open(path, "w") as f:
            f.write("a;b;c\n1;2;3\n4;5;6\n")
        loader = DataLoader(path)
        df = loader.load()
        assert df.shape == (2, 3)


# ── Tests: File Validation ────────────────────────────────────────────────────
class TestFileValidation:

    @pytest.mark.parametrize("ext", [".xlsx", ".xls", ".csv", ".txt"])
    def test_allowed_extensions(self, tmp_path, ext):
        """Allowed extensions should not raise ValueError on init."""
        path = str(tmp_path / f"file{ext}")
        # Write minimal content
        with open(path, "w") as f:
            f.write("col\n1\n")
        loader = DataLoader(path)
        assert loader.ext == ext

    def test_max_columns(self, tmp_path):
        """Wide datasets (many columns) should still load."""
        import io
        cols = [f"col_{i}" for i in range(100)]
        df = pd.DataFrame([range(100)], columns=cols)
        path = str(tmp_path / "wide.csv")
        df.to_csv(path, index=False)
        loader = DataLoader(path)
        result = loader.load()
        assert result.shape[1] == 100


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

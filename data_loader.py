"""
backend/data_loader.py
Handles file upload, reading, and type detection.
Supports: .xlsx, .xls, .csv, .txt, .json
"""

import os, io, json
import pandas as pd
from datetime import datetime


ALLOWED_EXT = {".xlsx", ".xls", ".csv", ".txt", ".json"}


class DataLoader:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.ext      = os.path.splitext(filepath)[1].lower()

    # ── Load ──────────────────────────────────────────────────────────────────
    def load(self) -> pd.DataFrame:
        if self.ext not in ALLOWED_EXT:
            raise ValueError(
                f"Format file '{self.ext}' tidak didukung. "
                f"Gunakan .xlsx, .csv, .txt, atau .json"
            )

        if self.ext in (".xlsx", ".xls"):
            df = pd.read_excel(self.filepath)
        elif self.ext == ".csv":
            df = self._read_csv()
        elif self.ext == ".json":
            df = self._read_json()
        else:  # .txt
            df = self._read_txt()

        df = self._auto_detect_types(df)
        return df

    def _read_csv(self) -> pd.DataFrame:
        for sep in [",", ";", "\t", "|"]:
            try:
                df = pd.read_csv(self.filepath, sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
        return pd.read_csv(self.filepath)

    def _read_txt(self) -> pd.DataFrame:
        for sep in ["\t", ",", ";", "|", " "]:
            try:
                df = pd.read_csv(self.filepath, sep=sep)
                if df.shape[1] > 1:
                    return df
            except Exception:
                continue
        return pd.read_csv(self.filepath, sep="\t")

    def _read_json(self) -> pd.DataFrame:
        with open(self.filepath, "r", encoding="utf-8") as f:
            raw = json.load(f)

        # Case 1: list of records  [{...}, {...}]
        if isinstance(raw, list):
            return pd.json_normalize(raw)

        # Case 2: dict of arrays  {"col1": [...], "col2": [...]}
        if isinstance(raw, dict):
            # Try direct DataFrame
            try:
                df = pd.DataFrame(raw)
                if not df.empty:
                    return df
            except Exception:
                pass
            # Try nested: find first list/dict value
            for key, val in raw.items():
                if isinstance(val, list):
                    df = pd.json_normalize(val)
                    if not df.empty:
                        return df
            # Flatten single-level dict as 1-row table
            return pd.DataFrame([raw])

        raise ValueError("Format JSON tidak dikenali. Gunakan array of objects atau object of arrays.")

    # ── Type Detection ────────────────────────────────────────────────────────
    def _auto_detect_types(self, df: pd.DataFrame) -> pd.DataFrame:
        for col in df.columns:
            if df[col].dtype == object:
                try:
                    converted = pd.to_datetime(df[col], infer_datetime_format=True)
                    df[col]   = converted
                    continue
                except Exception:
                    pass
                try:
                    df[col] = pd.to_numeric(df[col])
                except Exception:
                    pass
        return df

    # ── Info ──────────────────────────────────────────────────────────────────
    def get_info(self, df: pd.DataFrame) -> dict:
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
        dt_cols  = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
        missing  = int(df.isnull().sum().sum())

        col_info = []
        for col in df.columns:
            missing_col = int(df[col].isnull().sum())
            total_col   = int(len(df))
            if col in num_cols:
                ctype = "Numerical"
            elif col in dt_cols:
                ctype = "DateTime"
            else:
                ctype = "Categorical"
            col_info.append({
                "name"       : col,
                "dtype"      : str(df[col].dtype),
                "type"       : ctype,
                "missing"    : missing_col,
                "missing_pct": round(missing_col / total_col * 100, 1) if total_col else 0,
                "unique"     : int(df[col].nunique()),
            })

        return {
            "filename"        : os.path.basename(self.filepath),
            "rows"            : int(len(df)),
            "columns"         : int(len(df.columns)),
            "numeric_cols"    : len(num_cols),
            "numerical_cols"  : len(num_cols),
            "cat_cols"        : len(cat_cols),
            "categorical_cols": len(cat_cols),
            "datetime_cols"   : len(dt_cols),
            "missing_total"   : missing,
            "total_missing"   : missing,
            "missing_pct"     : round(missing / (len(df) * len(df.columns)) * 100, 2) if len(df) else 0,
            "size_kb"         : round(os.path.getsize(self.filepath) / 1024, 1),
            "filesize"        : str(round(os.path.getsize(self.filepath) / 1024, 1)) + " KB",
            "upload_time"     : datetime.now().strftime("%d %b %Y %H:%M"),
            "duplicates"      : int(df.duplicated().sum()),
            "dtypes"          : {c: str(t) for c, t in df.dtypes.items()},
            "column_names"    : list(df.columns),
            "column_info"     : col_info,
        }

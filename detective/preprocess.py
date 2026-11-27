"""
Preprocess module for Data Detective.
Performs column role detection, target classification/regression detection,
handling of missing values, high-cardinality categoricals, and feature scaling/encoding.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler

logger = logging.getLogger("data_detective.preprocess")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class PreprocessPipeline:
    """Automated preprocessing and feature encoding pipeline for tabular datasets."""

    def __init__(
        self,
        target_col: Optional[str] = None,
        id_col: Optional[str] = None,
        max_categories: int = 30,
        random_state: int = 42,
    ):
        self.target_col = target_col
        self.id_col = id_col
        self.max_categories = max_categories
        self.random_state = random_state

        self.id_cols_: List[str] = []
        self.num_cols_: List[str] = []
        self.cat_cols_: List[str] = []
        self.datetime_cols_: List[str] = []
        self.target_type_: str = "unknown"  # "classification", "regression", "none"
        self.target_encoder_: Optional[LabelEncoder] = None
        self.column_transformer_: Optional[ColumnTransformer] = None
        self.feature_names_: List[str] = []
        self.data_profile_: Dict[str, Any] = {}

    def detect_column_types(
        self, df: pd.DataFrame, target_col: Optional[str] = None, explicit_id: Optional[str] = None
    ) -> Dict[str, List[str]]:
        """Detect column roles: id-like, numeric, categorical, datetime."""
        id_cols = []
        num_cols = []
        cat_cols = []
        datetime_cols = []

        total_rows = len(df)
        cols_to_check = [c for c in df.columns if c != target_col]

        for col in cols_to_check:
            if explicit_id and col == explicit_id:
                id_cols.append(col)
                continue

            # Check if explicit or heuristic ID
            col_lower = str(col).lower()
            non_null_count = df[col].count()
            nunique = df[col].nunique(dropna=True)

            is_id_name = any(
                term in col_lower
                for term in ["id", "uuid", "guid", "index", "key", "identifier", "pk"]
            )

            # High cardinality relative to length (> 95% unique) or exact 1-to-1 if rows > 20
            if (
                total_rows > 20
                and non_null_count > 0
                and (
                    (nunique / non_null_count > 0.95 and (df[col].dtype == object or is_id_name))
                    or (nunique == total_rows and is_id_name)
                )
            ):
                id_cols.append(col)
                continue

            # Check datetime
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                datetime_cols.append(col)
                continue

            # Check if object column might be datetime
            if df[col].dtype == object and total_rows > 0:
                sample_s = df[col].dropna().head(20)
                if len(sample_s) > 0 and (
                    "date" in col_lower or "time" in col_lower or "timestamp" in col_lower
                ):
                    try:
                        pd.to_datetime(sample_s, errors="raise")
                        datetime_cols.append(col)
                        continue
                    except Exception:
                        pass

            # Numeric columns
            if pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col]):
                num_cols.append(col)
            else:
                cat_cols.append(col)

        return {
            "id_cols": id_cols,
            "num_cols": num_cols,
            "cat_cols": cat_cols,
            "datetime_cols": datetime_cols,
        }

    def detect_target_type(self, y: pd.Series) -> str:
        """Determines if the target is classification or regression."""
        non_null_y = y.dropna()
        if len(non_null_y) == 0:
            return "none"

        # Explicit non-numeric types are classification
        if (
            isinstance(y.dtype, pd.CategoricalDtype)
            or pd.api.types.is_object_dtype(y)
            or pd.api.types.is_bool_dtype(y)
            or pd.api.types.is_string_dtype(y)
        ):
            return "classification"

        # Numeric target
        nunique = non_null_y.nunique()
        total = len(non_null_y)

        # Few unique values (e.g. <= 20) or integer classification
        if nunique <= 20:
            return "classification"
        elif nunique / total < 0.05 and np.all(np.mod(non_null_y, 1) == 0):
            return "classification"
        else:
            return "regression"

    def compute_data_profile(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        col_types: Optional[Dict[str, List[str]]] = None,
    ) -> Dict[str, Any]:
        """Compute comprehensive statistical profile of the dataset."""
        total_rows, total_cols = df.shape
        missing_by_col = df.isnull().sum()
        missing_pct_by_col = (missing_by_col / total_rows * 100.0).round(2).to_dict()
        total_missing_cells = int(missing_by_col.sum())
        total_cells = total_rows * total_cols if total_rows > 0 and total_cols > 0 else 1
        overall_missing_pct = round(total_missing_cells / total_cells * 100.0, 2)

        dtypes_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}

        target_balance = {}
        target_type = "none"
        if target_col and target_col in df.columns:
            target_series = df[target_col]
            target_type = self.detect_target_type(target_series)
            if target_type == "classification":
                val_counts = target_series.value_counts(dropna=False, normalize=True).to_dict()
                target_balance = {
                    str(k): round(float(v) * 100.0, 2) for k, v in val_counts.items()
                }
            else:
                target_balance = {
                    "mean": float(target_series.mean()) if not target_series.empty else 0.0,
                    "std": float(target_series.std()) if not target_series.empty else 0.0,
                    "min": float(target_series.min()) if not target_series.empty else 0.0,
                    "max": float(target_series.max()) if not target_series.empty else 0.0,
                }

        col_types = col_types or self.detect_column_types(df, target_col, self.id_col)

        profile = {
            "total_rows": total_rows,
            "total_cols": total_cols,
            "overall_missing_pct": overall_missing_pct,
            "missing_pct_by_col": missing_pct_by_col,
            "dtypes": dtypes_dict,
            "target_col": target_col,
            "target_type": target_type,
            "class_balance": target_balance,
            "id_cols": col_types.get("id_cols", []),
            "num_cols": col_types.get("num_cols", []),
            "cat_cols": col_types.get("cat_cols", []),
            "datetime_cols": col_types.get("datetime_cols", []),
            "memory_usage_mb": round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2),
        }
        return profile

    def fit_transform(
        self,
        df: pd.DataFrame,
        target_col: Optional[str] = None,
        id_col: Optional[str] = None,
    ) -> Tuple[np.ndarray, Optional[np.ndarray], Dict[str, Any]]:
        """
        Fits transformer pipeline and returns transformed features (X),
        encoded target (y), and comprehensive profile & metadata.
        """
        self.target_col = target_col
        self.id_col = id_col

        df_work = df.copy()
        total_rows = len(df_work)

        # Column type detection
        type_detection = self.detect_column_types(df_work, self.target_col, self.id_col)
        self.id_cols_ = type_detection["id_cols"]
        self.num_cols_ = type_detection["num_cols"]
        self.cat_cols_ = type_detection["cat_cols"]
        self.datetime_cols_ = type_detection["datetime_cols"]

        # Compute profile
        self.data_profile_ = self.compute_data_profile(df_work, self.target_col, type_detection)

        # Process target
        y_array: Optional[np.ndarray] = None
        if self.target_col and self.target_col in df_work.columns:
            y_series = df_work[self.target_col]
            self.target_type_ = self.detect_target_type(y_series)
            self.data_profile_["target_type"] = self.target_type_

            if self.target_type_ == "classification":
                # Fill missing target with most frequent or a distinct placeholder
                y_clean = y_series.fillna("__MISSING_LABEL__").astype(str)
                self.target_encoder_ = LabelEncoder()
                y_array = self.target_encoder_.fit_transform(y_clean)
            elif self.target_type_ == "regression":
                y_array = pd.to_numeric(y_series, errors="coerce").fillna(y_series.median()).values
            else:
                y_array = None
        else:
            self.target_type_ = "none"

        # Feature columns: exclude target, ID columns, and pure datetimes from model features
        feature_cols = [c for c in self.num_cols_ + self.cat_cols_ if c != self.target_col]
        num_features = [c for c in self.num_cols_ if c != self.target_col]
        cat_features = [c for c in self.cat_cols_ if c != self.target_col]

        # Handle high cardinality categoricals safely before one-hot encoding
        for col in cat_features:
            val_counts = df_work[col].value_counts(dropna=True)
            if len(val_counts) > self.max_categories:
                top_k = set(val_counts.head(self.max_categories).index)
                df_work[col] = df_work[col].apply(
                    lambda v: v if pd.isna(v) or v in top_k else "__OTHER__"
                )
            df_work[col] = df_work[col].astype(str).replace("nan", np.nan)

        transformers = []
        if num_features:
            num_pipe = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="median")),
                    ("scaler", StandardScaler()),
                ]
            )
            transformers.append(("num", num_pipe, num_features))

        if cat_features:
            cat_pipe = Pipeline(
                [
                    ("imputer", SimpleImputer(strategy="most_frequent", fill_value="missing")),
                    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
                ]
            )
            transformers.append(("cat", cat_pipe, cat_features))

        if not transformers:
            # Fallback for empty or all-id datasets
            X_array = np.zeros((total_rows, 0))
            self.feature_names_ = []
            return X_array, y_array, self.data_profile_

        self.column_transformer_ = ColumnTransformer(
            transformers=transformers,
            remainder="drop",
        )

        X_array = self.column_transformer_.fit_transform(df_work)

        # Extract generated feature names
        try:
            self.feature_names_ = list(self.column_transformer_.get_feature_names_out())
        except Exception:
            self.feature_names_ = [f"feat_{i}" for i in range(X_array.shape[1])]

        logger.info(
            "Preprocess complete: %d rows, %d engineered features (%d numeric, %d categorical)",
            X_array.shape[0],
            X_array.shape[1],
            len(num_features),
            len(cat_features),
        )

        return X_array, y_array, self.data_profile_

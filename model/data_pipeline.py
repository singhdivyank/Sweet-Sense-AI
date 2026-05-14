"""
Extracts the diabetes dataset from BigQuery and produces stratified
train / validation / test splits using a single SQL query with
deterministic FARM_FINGERPRINT-based partitioning.

Splits
------
  train : 70 %
  val   : 15 %
  test  : 15 %

Dropped features (identified via ablation + VIF analysis)
----------------------------------------------------------
  _RFBMI5  : derived BMI flag, redundant with BMI
  Stroke   : low mutual information, noisy
  MentHlth : low mutual information, noisy

Target column
-------------
  isDiabetic  (multi-class: 0 = no diabetes, 1 = pre-diabetes, 2 = diabetes)
"""

import json

import pandas as pd

from google.auth import exceptions as auth_exceptions
from google.api_core import exceptions as api_exceptions
from google.cloud import bigquery
from google.oauth2 import service_account

from ..utils.consts import (
    DROP_COLS,
    EXTRACTION_QUERY,
    TRAIN_SPLIT,
    VAL_SPLIT,
    TARGET_COL,
)
from ..utils.logger import get_logger
from ..utils.settings import get_settings


class DataPrep:
    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.settings = get_settings()
        self._connect()
        self.splits: dict[str, pd.DataFrame] = {}

    def _connect(self):
        """Connect to BigQuery"""
        try:
            credentials = service_account.Credentials.from_service_account_file(
                str(self.settings.gcp_service_account), scopes=self.settings.gcp_scopes
            )
            self.client = bigquery.Client(
                project=self.settings.gcp_project, credentials=credentials
            )
        except FileNotFoundError as e:
            self.logger.error("Service account file not found: %s", str(e))
            raise
        except json.JSONDecodeError as e:
            self.logger.error("Service account file is not valid JSON: %s", str(e))
            raise
        except auth_exceptions.DefaultCredentialsError as e:
            self.logger.error("Invalid service account key structure: %s", str(e))
            raise
        except api_exceptions.GoogleAPICoreError as e:
            self.logger.error("Google API client initialization failed: %s", str(e))
            raise

    def fetch_data(self) -> None:
        """Execute the split query and return a single DataFrame with a `split` column."""

        if not self.client:
            self.logger.info("Could not initialise BigQuery service account")
            return None

        cols_to_drop = ",".join(col_name for col_name in DROP_COLS)
        table_id = f"{self.settings.gcp_project}.{self.settings.bq_dataset}.{self.settings.bq_table}"

        self.logger.info("Running BigQuery split query on `%s` ...", table_id)
        self.df = self.client.query(
            EXTRACTION_QUERY.format(
                exclude_cols=cols_to_drop,
                table_id=table_id,
                train_bound=TRAIN_SPLIT,
                val_bound=VAL_SPLIT,
            )
        ).to_dataframe()
        self.logger.info(
            "Fetched %d rows | columns: %s", len(self.df), list(self.df.columns)
        )

    def split_and_save(self):
        """Separate the DataFrame by the `split` column and write Parquet files."""
        
        df = self.df.copy()

        for name in ("train", "val", "test"):
            subset = (
                df[df["split"] == name].drop(columns=["split"]).reset_index(drop=True)
            )
            self.splits[name] = subset
            out_path = self.settings.output_dir / f"{name}.parquet"
            subset.to_parquet(out_path, index=False)

            self.logger.info(
                "%-5s → %6d rows | class distribution: %s",
                name,
                len(subset),
                subset[TARGET_COL].value_counts(normalise=True).sort_index().to_dict(),
            )

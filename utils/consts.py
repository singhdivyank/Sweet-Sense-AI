# Dataset columns
DROP_COLS = ["_RFBMI5", "Stroke", "MentHlth"]
TARGET_COL = "isDiabetic"
# split ratios
TRAIN_SPLIT = 69
VAL_SPLIT = 84
NUM_CLASSES = 3

N_ESTIMATORS = 300
LEARNING_RATE = 0.03
MAX_DEPTH = 6
RANDOM_STATE = 42

EXTRACTION_QUERY = """
WITH base_data AS (
    SELECT 
        * EXCEPT ({exclude_cols}),
        ABS(MOD(FARM_FINGERPRINT(CAST(ROW_NUMBER() OVER () AS STRING)), 100))
            AS _split_bucket
    FROM `{table_id}`
)

SELECT
    * EXCEPT (_split_bucket),
    CASE
        WHEN _split_bucket <= {train_bound} THEN 'train'
        WHEN _split_bucket <= {val_bound}   THEN 'val'
        ELSE                                    'test'
    END AS split
FROM base_data
""".strip()

# Dataset columns
DROP_COLS = ["_RFBMI5", "Stroke", "MentHlth"]
TARGET_COL = "isDiabetic"
# split ratios
TRAIN_SPLIT = 70
VAL_SPLIT = 85
NUM_CLASSES = 3

N_ESTIMATORS = 300
LEARNING_RATE = 0.03
MAX_DEPTH = 6
RANDOM_STATE = 42

EXTRACTION_QUERY = """
WITH base_data AS (
    SELECT * EXCEPT ({exclude_cols}) FROM `{table_id}`
),

split_data AS (
    SELECT *, 
            RAND() AS rand_val 
    FROM base_data
)

SELECT *,
        CASE 
            WHEN rand_val < {train_bound} THEN 'train'
            WHEN rand_val < {val_bound} THEN 'validation'
            ELSE 'test'
        END AS dataset_split
FROM split_data
""".strip()

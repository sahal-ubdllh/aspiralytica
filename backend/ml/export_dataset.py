import pandas as pd
from classifier import INTENT_DATA, SENTIMENT_DATA

# =========================
# EXPORT INTENT DATASET
# =========================
intent_df = pd.DataFrame({
    "text": INTENT_DATA["texts"],
    "label": INTENT_DATA["labels"]
})

intent_df.to_csv("intent_dataset.csv", index=False)

# =========================
# EXPORT SENTIMENT DATASET
# =========================
sentiment_df = pd.DataFrame({
    "text": SENTIMENT_DATA["texts"],
    "label": SENTIMENT_DATA["labels"]
})

sentiment_df.to_csv("sentiment_dataset.csv", index=False)

print("Dataset berhasil di-export!")
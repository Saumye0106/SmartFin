"""
Download the training data: "Give Me Some Credit" (Kaggle 2011 competition),
150,000 real borrowers labelled with whether they went 90+ days past due
within the following two years. Mirrored on OpenML (dataset 46929), which
needs no login.

    python -X utf8 risk_scorer/fetch_data.py      # from backend/

The CSV is not committed (it is git-ignored); only the trained model is.
"""

from __future__ import annotations

from pathlib import Path

OPENML_ID = 46929
DATA_PATH = Path(__file__).parent / "data" / "give_me_some_credit.csv"
SOURCE = {
    "name": "Give Me Some Credit",
    "openml_id": OPENML_ID,
    "openml_url": f"https://www.openml.org/d/{OPENML_ID}",
    "original_url": "https://www.kaggle.com/competitions/GiveMeSomeCredit",
    "label": "90+ days past due within the next 2 years",
    "population": "US consumer borrowers",
}


def fetch_and_save(path: Path = DATA_PATH):
    from sklearn.datasets import fetch_openml

    frame = fetch_openml(data_id=OPENML_ID, as_frame=True, parser="auto").frame
    if frame.shape != (150000, 11):
        raise RuntimeError(f"Unexpected dataset shape {frame.shape}; expected (150000, 11)")
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    return frame


if __name__ == "__main__":
    df = fetch_and_save()
    print(f"Saved {len(df):,} rows to {DATA_PATH}")

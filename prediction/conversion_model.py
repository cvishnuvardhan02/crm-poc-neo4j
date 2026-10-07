import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

load_dotenv()

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "crm_data.csv"


def load_data():
    df = pd.read_csv(DATA_PATH)

    closed = df[df["outcome"].isin(["Won", "Lost"])].copy()
    closed["target"] = (closed["outcome"] == "Won").astype(int)

    return df, closed


def employee_stats(closed):
    stats = (
        closed.groupby("employee_id")
        .agg(
            employee_win_rate=("target", "mean"),
            employee_wins=("target", "sum"),
            employee_opportunities=("target", "count"),
        )
        .reset_index()
    )

    return stats


def employee_domain_stats(closed):
    stats = (
        closed.groupby(["employee_id", "domain"])
        .agg(
            domain_win_rate=("target", "mean"),
            domain_wins=("target", "sum"),
            domain_opportunities=("target", "count"),
        )
        .reset_index()
    )

    return stats


def build_training_data():
    df, closed = load_data()

    emp_stats = employee_stats(closed)
    domain_stats = employee_domain_stats(closed)

    training = closed.merge(
        emp_stats,
        on="employee_id",
        how="left"
    )

    training = training.merge(
        domain_stats,
        on=["employee_id", "domain"],
        how="left"
    )

    training["domain_win_rate"] = training[
        "domain_win_rate"
    ].fillna(0)

    features = [
        "employee_id",
        "domain",
        "industry",
        "interaction_count",
        "meeting_count",
        "days_in_stage",
        "previous_customer_interactions",
        "opportunity_value",
        "employee_win_rate",
        "domain_win_rate",
    ]

    categorical = [
        "employee_id",
        "domain",
        "industry",
    ]

    numeric = [
        "interaction_count",
        "meeting_count",
        "days_in_stage",
        "previous_customer_interactions",
        "opportunity_value",
        "employee_win_rate",
        "domain_win_rate",
    ]

    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(
                    handle_unknown="ignore"
                ),
                categorical,
            ),
            (
                "numeric",
                StandardScaler(),
                numeric,
            ),
        ]
    )

    model = Pipeline(
        [
            ("preprocessor", preprocessor),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    C=0.5,
                ),
            ),
        ]
    )

    model.fit(
        training[features],
        training["target"],
    )

    return model, features, emp_stats, domain_stats


def prepare_opportunity(
    opportunity,
    employee_id,
    emp_stats,
    domain_stats,
):
    row = opportunity.copy()

    row["employee_id"] = employee_id

    employee_row = emp_stats[
        emp_stats["employee_id"] == employee_id
    ]

    if employee_row.empty:
        employee_win_rate = 0.0
    else:
        employee_win_rate = float(
            employee_row.iloc[0]["employee_win_rate"]
        )

    domain_row = domain_stats[
        (domain_stats["employee_id"] == employee_id)
        & (domain_stats["domain"] == row["domain"])
    ]

    if domain_row.empty:
        domain_win_rate = 0.0
    else:
        domain_win_rate = float(
            domain_row.iloc[0]["domain_win_rate"]
        )

    row["employee_win_rate"] = employee_win_rate
    row["domain_win_rate"] = domain_win_rate

    return row


def predict_opportunity(opportunity_id):
    df, _ = load_data()

    opportunity = df[
        df["opportunity_id"] == opportunity_id
    ]

    if opportunity.empty:
        raise ValueError(
            f"Opportunity {opportunity_id} not found"
        )

    model, features, emp_stats, domain_stats = (
        build_training_data()
    )

    row = opportunity.iloc[0]

    candidate = prepare_opportunity(
        row,
        row["employee_id"],
        emp_stats,
        domain_stats,
    )

    probability = float(
        model.predict_proba(
            pd.DataFrame([candidate])[features]
        )[0][1]
    )

    return {
        "opportunity_id": opportunity_id,
        "employee": row["employee_name"],
        "customer": row["customer_name"],
        "domain": row["domain"],
        "probability": round(probability, 4),
        "probability_percent": round(
            probability * 100,
            2
        ),
    }


def recommend_salespeople(opportunity_id):
    df, _ = load_data()

    opportunity = df[
        df["opportunity_id"] == opportunity_id
    ]

    if opportunity.empty:
        raise ValueError(
            f"Opportunity {opportunity_id} not found"
        )

    model, features, emp_stats, domain_stats = (
        build_training_data()
    )

    row = opportunity.iloc[0]

    employees = (
        df[
            ["employee_id", "employee_name"]
        ]
        .drop_duplicates()
        .to_dict("records")
    )

    results = []

    for employee in employees:

        candidate = prepare_opportunity(
            row,
            employee["employee_id"],
            emp_stats,
            domain_stats,
        )

        probability = float(
            model.predict_proba(
                pd.DataFrame([candidate])[features]
            )[0][1]
        )

        results.append(
            {
                "employee_id": employee["employee_id"],
                "employee": employee["employee_name"],
                "probability": round(
                    probability,
                    4
                ),
                "probability_percent": round(
                    probability * 100,
                    2
                ),
            }
        )

    return sorted(
        results,
        key=lambda x: x["probability"],
        reverse=True,
    )
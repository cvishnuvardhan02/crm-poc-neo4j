import os
import math

import requests
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API = os.getenv(
    "API_BASE_URL",
    "http://localhost:8000"
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="CRM Analytics Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ENTERPRISE CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GLOBAL
       ======================================================== */

    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 1600px;
    }


    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb;
    }


    /* ========================================================
       HEADERS
       ======================================================== */

    .main-title {
        font-size: 32px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0;
    }

    .sub-title {
        color: #6b7280;
        font-size: 14px;
        margin-top: 2px;
        margin-bottom: 25px;
    }

    .section-header {
        font-size: 19px;
        font-weight: 650;
        color: #111827;
        margin-top: 20px;
        margin-bottom: 10px;
    }


    /* ========================================================
       KPI CARDS
       ======================================================== */

    .kpi-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        min-height: 125px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .kpi-label {
        font-size: 13px;
        color: #6b7280;
        font-weight: 500;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
    }

    .kpi-description {
        font-size: 12px;
        color: #9ca3af;
        margin-top: 5px;
    }


    /* ========================================================
       GRAPH INFO
       ======================================================== */

    .graph-info {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
    }

    .node-property {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 7px;
        padding: 9px;
        margin-bottom: 7px;
        font-size: 13px;
    }


    /* ========================================================
       RECOMMENDATION
       ======================================================== */

    .recommendation-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    .recommendation-rank {
        font-size: 13px;
        color: #6b7280;
        font-weight: 600;
    }

    .recommendation-name {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
    }

    .recommendation-score {
        font-size: 28px;
        font-weight: 700;
        color: #111827;
    }

    .reason-card {
        background: #f9fafb;
        border-left: 3px solid #6b7280;
        padding: 10px 14px;
        margin-top: 7px;
        border-radius: 5px;
        font-size: 13px;
    }


    /* ========================================================
       STATUS
       ======================================================== */

    .status-online {
        color: #16a34a;
        font-weight: 600;
    }

    .status-offline {
        color: #dc2626;
        font-weight: 600;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    .stButton > button {
        border-radius: 7px;
        font-weight: 600;
    }


    /* ========================================================
       CREATE OPPORTUNITY
       ======================================================== */

    .create-summary {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 15px;
    }

    .create-summary-label {
        font-size: 12px;
        color: #6b7280;
        margin-bottom: 5px;
    }

    .create-summary-value {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================


def api_get(endpoint, timeout=10):
    """
    Safe GET request to FastAPI.
    """

    try:

        response = requests.get(
            f"{API}{endpoint}",
            timeout=timeout
        )

        if response.status_code != 200:

            try:
                detail = response.json()
            except Exception:
                detail = response.text

            return (
                None,
                f"API returned HTTP {response.status_code}: {detail}"
            )

        return response.json(), None

    except requests.exceptions.ConnectionError:

        return (
            None,
            f"Cannot connect to FastAPI at {API}"
        )

    except requests.exceptions.Timeout:

        return (
            None,
            "Request timed out."
        )

    except Exception as exc:

        return (
            None,
            str(exc)
        )


def api_post(endpoint, payload, timeout=15):
    """
    Safe POST request to FastAPI.
    """

    try:

        response = requests.post(
            f"{API}{endpoint}",
            json=payload,
            timeout=timeout
        )

        if response.status_code not in [200, 201]:

            try:
                detail = response.json()
            except Exception:
                detail = response.text

            return (
                None,
                f"API returned HTTP {response.status_code}: {detail}"
            )

        return response.json(), None

    except requests.exceptions.ConnectionError:

        return (
            None,
            f"Cannot connect to FastAPI at {API}"
        )

    except requests.exceptions.Timeout:

        return (
            None,
            "Request timed out."
        )

    except Exception as exc:

        return (
            None,
            str(exc)
        )


def format_currency(value):

    try:

        value = float(value)

        if value >= 10_000_000:
            return f"₹{value / 10_000_000:.2f}Cr"

        if value >= 100_000:
            return f"₹{value / 100_000:.2f}L"

        return f"₹{value:,.0f}"

    except Exception:

        return "₹0"


def safe_float(value, default=0):

    try:

        if value is None:
            return default

        value = float(value)

        if math.isnan(value) or math.isinf(value):
            return default

        return value

    except Exception:

        return default


def node_display_name(node):

    properties = node.get(
        "properties",
        {}
    )

    for key in [
        "name",
        "employee_name",
        "customer_name",
        "opportunity_name",
        "product_name",
        "domain_name",
        "stage_name",
        "title",
        "id",
    ]:

        value = properties.get(key)

        if value not in [None, ""] and str(value).strip().lower() not in {"none", "null", "nan"}:
            return str(value)

    return str(
        node.get(
            "id",
            "Unknown"
        )
    )


def node_label(node):
    """Return a safe display label for Neo4j nodes across API response shapes."""
    labels = node.get("labels", [])
    if isinstance(labels, str):
        labels = [labels]
    if isinstance(labels, (list, tuple)):
        clean_labels = [str(label).strip() for label in labels if label not in (None, "")]
        if clean_labels:
            return clean_labels[0]
    return "Node"


# ============================================================
# API HEALTH
# ============================================================

health, health_error = api_get(
    "/health/neo4j"
)

neo4j_online = (
    health is not None
    and health.get("neo4j") is True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown(
        """
        <div style="display:flex;align-items:center;gap:10px;font-size:24px;font-weight:750;white-space:nowrap;">
            <span style="font-size:27px;color:#93c5fd;">◈</span>
            <span>CRM Analytics</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LOAD CRM DATA
# ============================================================

DATA_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "data",
    "crm_data.csv"
)

try:

    data = pd.read_csv(
        DATA_PATH
    )

except Exception:

    data = pd.DataFrame()


# ============================================================
# LOAD EMPLOYEES
# ============================================================

employees, employees_error = api_get(
    "/employees",
    timeout=10
)

if employees is None:
    employees = []


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">CRM Analytics Engine</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="sub-title">
        Enterprise CRM intelligence powered by Neo4j graph analytics
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# EXECUTIVE KPI CALCULATIONS
# ============================================================

if not data.empty:

    total_customers = (
        data["customer_id"].nunique()
        if "customer_id" in data.columns
        else 0
    )

    if (
        "stage" in data.columns
        and "opportunity_value" in data.columns
    ):

        pipeline = data.loc[
            data["stage"]
            .astype(str)
            .str.lower()
            == "open",
            "opportunity_value"
        ].sum()

    else:

        pipeline = 0

    if "outcome" in data.columns:

        closed = data[
            data["outcome"].isin(
                ["Won", "Lost"]
            )
        ]

        if not closed.empty:

            win_rate = (
                closed["outcome"]
                .eq("Won")
                .mean()
            )

        else:

            win_rate = 0

    else:

        win_rate = 0

    revenue_won = (
        data.loc[
            data["outcome"] == "Won",
            "opportunity_value"
        ].sum()
        if (
            "outcome" in data.columns
            and "opportunity_value" in data.columns
        )
        else 0
    )

    open_opportunities = (
        len(
            data[
                data["stage"]
                .astype(str)
                .str.lower()
                == "open"
            ]
        )
        if "stage" in data.columns
        else 0
    )

else:

    total_customers = 0
    pipeline = 0
    win_rate = 0
    revenue_won = 0
    open_opportunities = 0


# ============================================================
# KPI CARDS
# ============================================================

k1, k2, k3, k4, k5 = st.columns(5)


with k1:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">CUSTOMERS</div>
            <div class="kpi-value">{total_customers}</div>
            <div class="kpi-description">
                Active CRM entities
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k2:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">OPEN PIPELINE</div>
            <div class="kpi-value">
                {format_currency(pipeline)}
            </div>
            <div class="kpi-description">
                Current opportunity value
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k3:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">WIN RATE</div>
            <div class="kpi-value">
                {win_rate:.0%}
            </div>
            <div class="kpi-description">
                Closed opportunities
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k4:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">REVENUE WON</div>
            <div class="kpi-value">
                {format_currency(revenue_won)}
            </div>
            <div class="kpi-description">
                Closed won revenue
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


with k5:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">OPEN OPPORTUNITIES</div>
            <div class="kpi-value">
                {open_opportunities}
            </div>
            <div class="kpi-description">
                Active sales opportunities
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.divider()


# ============================================================
# NAVIGATION
# ============================================================

tabs = st.tabs(
    [
        "Executive Dashboard",
        "Salesperson Analytics",
        "Recommendations",
        "Create Opportunity",
        "Opportunity Intelligence",
        "Graph Explorer",
    ]
)


# ============================================================
# TAB 1 — EXECUTIVE DASHBOARD
# ============================================================

with tabs[0]:

    st.markdown(
        '<div class="section-header">Executive Overview</div>',
        unsafe_allow_html=True
    )

    if data.empty:

        st.warning(
            "CRM dataset could not be loaded."
        )

    else:

        left, right = st.columns(2)


        # ----------------------------------------------------
        # PIPELINE BY DOMAIN
        # ----------------------------------------------------

        with left:

            st.markdown(
                "#### Pipeline by Domain"
            )

            if (
                "domain" in data.columns
                and "opportunity_value" in data.columns
                and "stage" in data.columns
            ):

                domain_pipeline = (
                    data[
                        data["stage"]
                        .astype(str)
                        .str.lower()
                        == "open"
                    ]
                    .groupby("domain")[
                        "opportunity_value"
                    ]
                    .sum()
                    .sort_values(
                        ascending=True
                    )
                )

                fig = go.Figure(
                    go.Bar(
                        x=domain_pipeline.values,
                        y=domain_pipeline.index,
                        orientation="h",
                        text=[
                            format_currency(x)
                            for x in domain_pipeline.values
                        ],
                        textposition="outside",
                    )
                )

                fig.update_layout(
                    height=400,
                    margin=dict(
                        l=10,
                        r=80,
                        t=20,
                        b=20,
                    ),
                    xaxis_title="Pipeline Value",
                    yaxis_title="",
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


        # ----------------------------------------------------
        # OPPORTUNITIES BY STAGE
        # ----------------------------------------------------

        with right:

            st.markdown(
                "#### Opportunities by Stage"
            )

            if "stage" in data.columns:

                stage_counts = (
                    data["stage"]
                    .value_counts()
                )

                fig = go.Figure(
                    go.Pie(
                        labels=stage_counts.index,
                        values=stage_counts.values,
                        hole=0.55,
                    )
                )

                fig.update_layout(
                    height=400,
                    margin=dict(
                        l=10,
                        r=10,
                        t=20,
                        b=20,
                    ),
                    paper_bgcolor="white",
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True
                )


        # ----------------------------------------------------
        # OPEN PIPELINE
        # ----------------------------------------------------

        st.markdown(
            "#### Open Pipeline"
        )

        if "stage" in data.columns:

            open_df = data[
                data["stage"]
                .astype(str)
                .str.lower()
                == "open"
            ].copy()

            display_columns = [
                col
                for col in [
                    "opportunity_id",
                    "opportunity_name",
                    "customer_name",
                    "employee_name",
                    "domain",
                    "opportunity_value",
                ]
                if col in open_df.columns
            ]

            st.dataframe(
                open_df[display_columns],
                use_container_width=True,
                hide_index=True,
            )


# ============================================================
# TAB 2 — SALESPERSON ANALYTICS
# ============================================================

with tabs[1]:

    st.markdown(
        '<div class="section-header">Salesperson Intelligence</div>',
        unsafe_allow_html=True
    )

    if not employees:

        st.warning(
            "No employees returned from API."
        )

    else:

        names = {
            employee["name"]:
                employee["id"]
            for employee in employees
        }

        selected = st.selectbox(
            "Salesperson",
            list(names.keys()),
            key="salesperson"
        )

        employee_id = names[selected]

        performance, error = api_get(
            f"/employees/{employee_id}/performance",
            timeout=10
        )

        if error:

            st.error(error)

        else:

            a, b, c, d = st.columns(4)

            with a:

                st.metric(
                    "Win Rate",
                    f"{safe_float(performance.get('win_rate')):.0%}"
                )

            with b:

                st.metric(
                    "Wins",
                    performance.get(
                        "wins",
                        0
                    )
                )

            with c:

                st.metric(
                    "Opportunities",
                    performance.get(
                        "opportunities",
                        0
                    )
                )

            with d:

                st.metric(
                    "Revenue Won",
                    format_currency(
                        performance.get(
                            "revenue_won",
                            0
                        )
                    )
                )

            st.divider()

            st.markdown("#### Performance Details")
            performance_rows = [
                {"Metric": "Salesperson", "Value": performance.get("employee", selected)},
                {"Metric": "Employee ID", "Value": performance.get("employee_id", employee_id)},
                {"Metric": "Wins", "Value": performance.get("wins", 0)},
                {"Metric": "Losses", "Value": performance.get("losses", 0)},
                {"Metric": "Open Opportunities", "Value": performance.get("open", 0)},
                {"Metric": "Total Opportunities", "Value": performance.get("opportunities", 0)},
                {"Metric": "Win Rate", "Value": f"{safe_float(performance.get('win_rate')):.1%}"},
                {"Metric": "Revenue Won", "Value": format_currency(performance.get("revenue_won", 0))},
                {"Metric": "Average Deal Size", "Value": format_currency(performance.get("average_deal_size", 0))},
            ]
            st.dataframe(
                pd.DataFrame(performance_rows),
                use_container_width=True,
                hide_index=True,
                column_config={"Metric": st.column_config.TextColumn("Metric", width="medium"),
                               "Value": st.column_config.TextColumn("Value", width="large")},
            )


# ============================================================
# TAB 3 — DOMAIN RECOMMENDATIONS
# ============================================================

with tabs[2]:

    st.markdown(
        '<div class="section-header">Graph-Based Domain Recommendations</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Recommendations are generated from domain relationships "
        "and salesperson historical performance."
    )

    if not employees:

        st.warning(
            "No employees available."
        )

    else:

        names = {
            employee["name"]:
                employee["id"]
            for employee in employees
        }

        selected = st.selectbox(
            "Salesperson",
            list(names.keys()),
            key="recommendation_employee"
        )

        employee_id = names[selected]

        result, error = api_get(
            f"/employees/{employee_id}/recommendations",
            timeout=15
        )

        if error:

            st.error(error)

        else:

            recommendations = result.get(
                "recommendations",
                []
            )

            if not recommendations:

                st.info(
                    "No domain recommendations available."
                )

            else:
                recommendation_rows = []
                for idx, rec in enumerate(recommendations, 1):
                    score = safe_float(rec.get("score"))
                    recommendation_rows.append({
                        "Rank": idx,
                        "Recommended Domain": rec.get("domain", "Unknown"),
                        "Likelihood Score": f"{score:.1%}",
                        "Related To": rec.get("source_domain", "Unknown"),
                        "Reason": "; ".join(str(x) for x in (rec.get("reason") or [])),
                    })
                st.dataframe(
                    pd.DataFrame(recommendation_rows),
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Rank": st.column_config.NumberColumn("Rank", format="%d", width="small"),
                        "Recommended Domain": st.column_config.TextColumn("Recommended Domain", width="medium"),
                        "Likelihood Score": st.column_config.TextColumn("Likelihood Score", width="small"),
                        "Related To": st.column_config.TextColumn("Related To", width="medium"),
                        "Reason": st.column_config.TextColumn("Why it is recommended", width="large"),
                    },
                )
                st.caption("Scores are weighted recommendation scores, not calibrated statistical probabilities.")


# ============================================================
# TAB 4 — CREATE OPPORTUNITY
# ============================================================

with tabs[3]:

    st.markdown(
        '<div class="section-header">Create Opportunity</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Create a new CRM opportunity and automatically "
        "generate graph-based domain intelligence."
    )

    # ========================================================
    # FORM
    # ========================================================

    with st.form("create_opportunity_form"):

        left, right = st.columns(2)

        # ----------------------------------------------------
        # LEFT
        # ----------------------------------------------------

        with left:

            opportunity_name = st.text_input(
                "Opportunity Name",
                placeholder="e.g. Digital Banking Transformation",
                key="create_opportunity_name"
            )

            customer_name = st.text_input(
                "Customer",
                placeholder="e.g. HDFC Bank",
                key="create_customer_name"
            )

            domain_name = st.text_input(
                "Business Domain",
                placeholder="e.g. Fintech",
                key="create_domain_name"
            )

        # ----------------------------------------------------
        # RIGHT
        # ----------------------------------------------------

        with right:

            opportunity_value = st.number_input(
                "Opportunity Value",
                min_value=0.0,
                step=50000.0,
                value=500000.0,
                format="%.0f",
                key="create_opportunity_value"
            )

            salesperson_options = {
                "Auto Recommend": None
            }

            for employee in employees:

                salesperson_options[
                    employee.get(
                        "name",
                        employee.get("id")
                    )
                ] = employee.get("id")

            selected_salesperson = st.selectbox(
                "Salesperson",
                list(
                    salesperson_options.keys()
                ),
                key="create_salesperson"
            )

        st.markdown("---")

        submitted = st.form_submit_button(
            "Create Opportunity",
            type="primary",
            use_container_width=True
        )


    # ========================================================
    # CREATE OPPORTUNITY
    # ========================================================

    if submitted:

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not opportunity_name.strip():

            st.error(
                "Opportunity name is required."
            )

        elif not customer_name.strip():

            st.error(
                "Customer name is required."
            )

        elif not domain_name.strip():

            st.error(
                "Business domain is required."
            )

        elif opportunity_value <= 0:

            st.error(
                "Opportunity value must be greater than zero."
            )

        else:

            payload = {

                "name":
                    opportunity_name.strip(),

                "customer_name":
                    customer_name.strip(),

                "domain":
                    domain_name.strip(),

                "value":
                    float(opportunity_value),

                "employee_id":
                    salesperson_options[
                        selected_salesperson
                    ]
            }

            # ------------------------------------------------
            # STEP 1 — CREATE OPPORTUNITY
            # ------------------------------------------------

            with st.spinner(
                "Creating opportunity in Neo4j..."
            ):

                created, create_error = api_post(
                    "/opportunities",
                    payload,
                    timeout=20
                )

            if create_error:

                st.error(
                    f"Opportunity creation failed: "
                    f"{create_error}"
                )

            else:

                opportunity = created.get(
                    "opportunity",
                    {}
                )

                opportunity_id = opportunity.get(
                    "opportunity_id"
                )

                st.success(
                    f"Opportunity {opportunity_id} "
                    f"created successfully."
                )

                # ------------------------------------------------
                # CREATED OPPORTUNITY SUMMARY
                # ------------------------------------------------

                c1, c2, c3, c4 = st.columns(4)

                with c1:

                    st.metric(
                        "Opportunity ID",
                        opportunity_id
                    )

                with c2:

                    st.metric(
                        "Customer",
                        opportunity.get(
                            "customer_name",
                            customer_name
                        )
                    )

                with c3:

                    st.metric(
                        "Domain",
                        opportunity.get(
                            "domain",
                            domain_name
                        )
                    )

                with c4:

                    st.metric(
                        "Value",
                        format_currency(
                            opportunity.get(
                                "opportunity_value",
                                opportunity_value
                            )
                        )
                    )

                st.divider()

                # ------------------------------------------------
                # STEP 2 — DOMAIN SIMILARITY
                # ------------------------------------------------

                st.markdown(
                    "#### Domain Intelligence"
                )

                st.caption(
                    "Generating semantic similarity relationships "
                    "for the new domain."
                )

                with st.spinner(
                    "Calculating domain similarity..."
                ):

                    similarity_result, similarity_error = api_post(
                         f"/domains/{domain_name.strip()}/similarity",
                        {},
                         timeout=60
                )

                if similarity_error:

                    st.warning(
                        "Opportunity was created, but domain "
                        "similarity could not be generated."
                    )

                    st.code(
                        similarity_error
                    )

                else:

                    relationships = similarity_result.get(
                        "relationships",
                        []
                    )

                    relationships_created = (
                        similarity_result.get(
                            "relationships_created",
                            len(relationships)
                        )
                    )

                    st.success(
                        f"{relationships_created} domain similarity "
                        f"relationships generated."
                    )

                    if relationships:

                        similarity_rows = []

                        for relationship in relationships:

                            similarity_rows.append(
                                {
                                    "Source Domain":
                                        relationship.get(
                                            "source"
                                        ),

                                    "Target Domain":
                                        relationship.get(
                                            "target"
                                        ),

                                    "Similarity":
                                        f"{safe_float(
                                            relationship.get(
                                                "score"
                                            )
                                        ):.1%}",

                                    "Method":
                                        relationship.get(
                                            "method",
                                            "semantic_embedding"
                                        )
                                }
                            )

                        st.dataframe(
                            pd.DataFrame(
                                similarity_rows
                            ),
                            use_container_width=True,
                            hide_index=True
                        )

                    else:

                        st.info(
                            "No similar domains crossed the "
                            "configured similarity threshold."
                        )

                    # ------------------------------------------------
                    # SHOW STORED SIMILAR DOMAINS FROM NEO4J
                    # ------------------------------------------------

                    similar_domains, similar_error = api_get(
                        f"/domains/{domain_name.strip()}/similar",
                        timeout=20
                    )

                    if not similar_error and similar_domains:

                        similar_list = similar_domains.get(
                            "similar_domains",
                            []
                        )

                        if similar_list:

                            st.markdown(
                                "#### Similar Domains in Neo4j"
                            )

                            similar_rows = []

                            for item in similar_list:

                                similar_rows.append(
                                    {
                                        "Domain":
                                            item.get(
                                                "target_domain",
                                                ""
                                            ),

                                        "Similarity":
                                            f"{safe_float(
                                                item.get(
                                                    "score",
                                                    0
                                                )
                                            ):.1%}"
                                    }
                                )

                            if similar_rows:

                                st.dataframe(
                                    pd.DataFrame(
                                        similar_rows
                                    ),
                                    use_container_width=True,
                                    hide_index=True
                                )

                                st.caption(
                                    "Similarity method: Semantic Embedding • "
                                    "Model: all-MiniLM-L6-v2"
                                )

                # ------------------------------------------------
                # STEP 3 — SALESPERSON RECOMMENDATION
                # ------------------------------------------------

                if selected_salesperson == "Auto Recommend":

                    st.divider()

                    st.markdown(
                        "#### Recommended Salesperson"
                    )

                    with st.spinner(
                        "Ranking salespeople using graph intelligence..."
                    ):

                        ranking, ranking_error = api_get(
                            f"/recommendations/opportunities/"
                            f"{opportunity_id}/salespeople",
                            timeout=30
                        )

                    if ranking_error:

                        st.warning(
                            "Opportunity created successfully, "
                            "but salesperson recommendation failed."
                        )

                        st.code(
                            ranking_error
                        )

                    else:

                        salespeople = ranking.get(
                            "salespeople",
                            []
                        )

                        if salespeople:

                            top = salespeople[0]

                            top_name = top.get(
                                "employee_name",
                                "Unknown"
                            )

                            top_score = safe_float(
                                top.get(
                                    "likelihood_score_percent"
                                )
                            )

                            st.success(
                                f"Recommended Salesperson: "
                                f"**{top_name}** — "
                                f"{top_score:.1f}%"
                            )

                            # ------------------------------------
                            # SCORE BREAKDOWN
                            # ------------------------------------

                            c1, c2, c3 = st.columns(3)

                            with c1:

                                st.metric(
                                    "Domain Similarity",
                                    f"{safe_float(
                                        top.get(
                                            "domain_similarity"
                                        )
                                    ):.0%}"
                                )

                                st.caption(
                                    "Weight: 50%"
                                )

                            with c2:

                                st.metric(
                                    "Peer Success",
                                    f"{safe_float(
                                        top.get(
                                            "peer_success"
                                        )
                                    ):.0%}"
                                )

                                st.caption(
                                    "Weight: 30%"
                                )

                            with c3:

                                st.metric(
                                    "Historical Performance",
                                    f"{safe_float(
                                        top.get(
                                            "historical_performance"
                                        )
                                    ):.0%}"
                                )

                                st.caption(
                                    "Weight: 20%"
                                )

                            # ------------------------------------
                            # RANKING TABLE
                            # ------------------------------------

                            st.markdown(
                                "##### Salesperson Ranking"
                            )

                            ranking_rows = []

                            for salesperson in salespeople:

                                ranking_rows.append(
                                    {
                                        "Rank":
                                            salesperson.get(
                                                "rank"
                                            ),

                                        "Salesperson":
                                            salesperson.get(
                                                "employee_name"
                                            ),

                                        "Score":
                                            f"{safe_float(
                                                salesperson.get(
                                                    "likelihood_score_percent"
                                                )
                                            ):.1f}%",

                                        "Domain Similarity":
                                            f"{safe_float(
                                                salesperson.get(
                                                    "domain_similarity"
                                                )
                                            ):.1%}",

                                        "Peer Success":
                                            f"{safe_float(
                                                salesperson.get(
                                                    "peer_success"
                                                )
                                            ):.1%}",

                                        "Historical Performance":
                                            f"{safe_float(
                                                salesperson.get(
                                                    "historical_performance"
                                                )
                                            ):.1%}"
                                    }
                                )

                            st.dataframe(
                                pd.DataFrame(
                                    ranking_rows
                                ),
                                use_container_width=True,
                                hide_index=True
                            )

                            # ------------------------------------
                            # EXPLAINABILITY
                            # ------------------------------------

                            if top.get("cold_start", False):


                                st.info(


                                    "Cold-start domain: no historical domain-specific "


                                    "evidence was found. The company-wide historical "


                                    "baseline was used for peer success."


                                )



                            reasons = top.get(


                                "reasons",


                                []


                            )



                            if reasons:

                                st.markdown(
                                    "##### Why this salesperson?"
                                )

                                for reason in reasons:
                                    st.markdown(f"- ✓ {reason}")

                        else:

                            st.info(
                                "No salesperson recommendations "
                                "were generated."
                            )

                else:

                    st.info(
                        f"Opportunity assigned to "
                        f"**{selected_salesperson}**."
                    )


# ============================================================
# TAB 5 — OPPORTUNITY INTELLIGENCE
# ============================================================

with tabs[4]:

    st.markdown(
        '<div class="section-header">Opportunity Intelligence</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Select an open opportunity to see likelihood score "
        "and graph-based salesperson ranking."
    )

    if data.empty:

        st.warning(
            "CRM dataset unavailable."
        )

    else:

        if "stage" in data.columns:

            opportunities = data[
                data["stage"]
                .astype(str)
                .str.lower()
                == "open"
            ].copy()

        else:

            opportunities = pd.DataFrame()


        if opportunities.empty:

            st.info(
                "No open opportunities available."
            )

        else:

            # ------------------------------------------------
            # OPPORTUNITY SELECTOR
            # ------------------------------------------------

            opportunity_options = {}

            for _, opportunity in opportunities.iterrows():

                opportunity_id = str(
                    opportunity.get(
                        "opportunity_id",
                        ""
                    )
                )

                opportunity_name = str(
                    opportunity.get(
                        "opportunity_name",
                        opportunity_id
                    )
                )

                opportunity_options[
                    f"{opportunity_id} — {opportunity_name}"
                ] = opportunity_id


            selected_label = st.selectbox(
                "Opportunity",
                list(
                    opportunity_options.keys()
                ),
                key="prediction_opportunity"
            )

            selected_opp = opportunity_options[
                selected_label
            ]


            row = opportunities[
                opportunities["opportunity_id"]
                .astype(str)
                == str(selected_opp)
            ].iloc[0]


            # ------------------------------------------------
            # OPPORTUNITY HEADER
            # ------------------------------------------------

            header_a, header_b, header_c = st.columns([2, 1, 1])
            with header_a:
                st.markdown(f"### {row.get('opportunity_name', selected_opp)}")
                st.caption(f"Opportunity ID: {selected_opp}")
            with header_b:
                st.metric("Customer", str(row.get("customer_name", "Unknown")))
            with header_c:
                st.metric("Domain", str(row.get("domain", "Unknown")))

            # ------------------------------------------------
            # CONVERSION PREDICTION
            # ------------------------------------------------

            prediction, prediction_error = api_get(
                f"/opportunities/{selected_opp}/prediction",
                timeout=15
            )

            if prediction_error:

                st.warning(
                    f"Likelihood score unavailable: "
                    f"{prediction_error}"
                )

            else:

                probability = safe_float(
                    prediction.get(
                        "likelihood_score_percent",
                        prediction.get("probability_percent", prediction.get("likelihood_score", 0))
                    )
                )

                p1, p2, p3 = st.columns(3)

                with p1:

                    st.metric(
                        "Likelihood Score",
                        f"{probability:.1f}%"
                    )

                with p2:

                    st.metric(
                        "Opportunity Value",
                        format_currency(
                            row.get(
                                "opportunity_value",
                                0
                            )
                        )
                    )

                with p3:

                    expected_value = (
                        probability / 100
                    ) * safe_float(
                        row.get(
                            "opportunity_value",
                            0
                        )
                    )

                    st.metric(
                        "Expected Revenue",
                        format_currency(
                            expected_value
                        )
                    )


            st.divider()


            # =================================================
            # GRAPH-BASED SALESPERSON RECOMMENDATION
            # =================================================

            st.markdown(
                "#### Recommended Salespeople"
            )

            st.caption(
                "Ranking formula: "
                "50% Domain Similarity + "
                "30% Peer Success + "
                "20% Historical Performance"
            )


            ranking, ranking_error = api_get(
                f"/recommendations/opportunities/"
                f"{selected_opp}/salespeople",
                timeout=20
            )


            if ranking_error:

                st.error(
                    f"Salesperson recommendation failed: "
                    f"{ranking_error}"
                )

            else:

                salespeople = ranking.get(
                    "salespeople",
                    []
                )


                if not salespeople:

                    st.info(
                        "No salesperson recommendations "
                        "available for this opportunity."
                    )

                else:

                    # -----------------------------------------
                    # TOP RECOMMENDATION
                    # -----------------------------------------

                    top = salespeople[0]

                    top_score = safe_float(
                        top.get(
                            "likelihood_score_percent"
                        )
                    )

                    st.success(
                        f"Recommended Salesperson: "
                        f"**{top.get('employee_name', 'Unknown')}** "
                        f"— {top_score:.1f}%"
                    )


                    # -----------------------------------------
                    # SCORE BREAKDOWN
                    # -----------------------------------------

                    st.markdown(
                        "##### Recommendation Score Breakdown"
                    )

                    c1, c2, c3 = st.columns(3)


                    with c1:

                        domain_similarity = safe_float(
                            top.get(
                                "domain_similarity"
                            )
                        )

                        st.metric(
                            "Domain Similarity",
                            f"{domain_similarity:.0%}"
                        )

                        st.caption(
                            "Weight: 50%"
                        )


                    with c2:

                        peer_success = safe_float(
                            top.get(
                                "peer_success"
                            )
                        )

                        st.metric(
                            "Peer Success",
                            f"{peer_success:.0%}"
                        )

                        st.caption(
                            "Weight: 30%"
                        )


                    with c3:

                        historical = safe_float(
                            top.get(
                                "historical_performance"
                            )
                        )

                        st.metric(
                            "Historical Performance",
                            f"{historical:.0%}"
                        )

                        st.caption(
                            "Weight: 20%"
                        )


                    # -----------------------------------------
                    # ACTUAL SCORE CALCULATION
                    # -----------------------------------------

                    calculated_score = (
                        0.50 * domain_similarity
                        +
                        0.30 * peer_success
                        +
                        0.20 * historical
                    )

                    st.progress(
                        min(
                            max(
                                calculated_score,
                                0
                            ),
                            1
                        )
                    )

                    st.caption(
                        f"Final graph likelihood score: "
                        f"**{calculated_score:.1%}**"
                    )


                    # -----------------------------------------
                    # EXPLAINABILITY
                    # -----------------------------------------

                    st.markdown(
                        "##### Why was this salesperson recommended?"
                    )

                    if top.get("cold_start", False):


                        st.info(


                            "Cold-start domain: no historical domain-specific "


                            "evidence was found. The company-wide historical "


                            "baseline was used for peer success."


                        )



                    reasons = top.get(


                        "reasons",


                        []


                    )



                    if reasons:

                        for reason in reasons:
                            st.markdown(f"- ✓ {reason}")

                    else:

                        st.info(
                            "Recommendation is based on "
                            "available graph evidence."
                        )


                    st.divider()


                    # -----------------------------------------
                    # SALESPERSON RANKING
                    # -----------------------------------------

                    st.markdown(
                        "##### Salesperson Ranking"
                    )

                    ranking_rows = []

                    for salesperson in salespeople:

                        ranking_rows.append(
                            {
                                "Rank":
                                    salesperson.get(
                                        "rank",
                                        ""
                                    ),

                                "Salesperson":
                                    salesperson.get(
                                        "employee_name",
                                        "Unknown"
                                    ),

                                "Likelihood Score":
                                    f"{safe_float(
                                        salesperson.get(
                                            'likelihood_score_percent'
                                        )
                                    ):.1f}%",

                                "Domain Similarity":
                                    f"{safe_float(
                                        salesperson.get(
                                            'domain_similarity'
                                        )
                                    ):.1%}",

                                "Peer Success":
                                    f"{safe_float(
                                        salesperson.get(
                                            'peer_success'
                                        )
                                    ):.1%}",

                                "Historical Performance":
                                    f"{safe_float(
                                        salesperson.get(
                                            'historical_performance'
                                        )
                                    ):.1%}",

                                "Wins":
                                    salesperson.get(
                                        "wins",
                                        0
                                    ),

                                "Opportunities":
                                    salesperson.get(
                                        "total_opportunities",
                                        0
                                    )
                            }
                        )


                    ranking_df = pd.DataFrame(
                        ranking_rows
                    )

                    st.dataframe(
                        ranking_df,
                        use_container_width=True,
                        hide_index=True
                    )


                    # -----------------------------------------
                    # DETAILED EXPLANATION
                    # -----------------------------------------

                    st.markdown(
                        "##### Detailed Recommendation Evidence"
                    )

                    selected_salesperson = st.selectbox(
                        "Inspect salesperson",
                        [
                            x.get(
                                "employee_name",
                                "Unknown"
                            )
                            for x in salespeople
                        ],
                        key="inspect_salesperson"
                    )


                    selected_result = next(
                        (
                            x
                            for x in salespeople
                            if x.get(
                                "employee_name"
                            )
                            == selected_salesperson
                        ),
                        None
                    )


                    if selected_result:

                        left, right = st.columns(2)


                        with left:

                            st.markdown(
                                "**Domain Evidence**"
                            )

                            domain_evidence = (
                                selected_result.get(
                                    "domain_evidence",
                                    []
                                )
                                or []
                            )


                            if domain_evidence:

                                evidence_rows = []

                                for evidence in domain_evidence:

                                    evidence_rows.append(
                                        {
                                            "Domain":
                                                evidence.get(
                                                    "domain",
                                                    ""
                                                ),

                                            "Outcome":
                                                evidence.get(
                                                    "outcome",
                                                    ""
                                                ),

                                            "Similarity":
                                                f"{safe_float(
                                                    evidence.get(
                                                        "similarity"
                                                    )
                                                ):.1%}"
                                        }
                                    )


                                evidence_df = pd.DataFrame(evidence_rows).drop_duplicates()
                                st.dataframe(
                                    evidence_df,
                                    use_container_width=True,
                                    hide_index=True
                                )

                            else:

                                st.info(
                                    "No domain evidence available."
                                )


                        with right:

                            st.markdown(
                                "**Peer Evidence**"
                            )

                            peer_evidence = (
                                selected_result.get(
                                    "peer_evidence",
                                    []
                                )
                                or []
                            )


                            if peer_evidence:

                                peer_rows = []

                                for evidence in peer_evidence:

                                    peer_rows.append(
                                        {
                                            "Salesperson":
                                                evidence.get(
                                                    "employee",
                                                    ""
                                                ),

                                            "Domain":
                                                evidence.get(
                                                    "domain",
                                                    ""
                                                ),

                                            "Outcome":
                                                evidence.get(
                                                    "outcome",
                                                    ""
                                                ),

                                            "Similarity":
                                                f"{safe_float(
                                                    evidence.get(
                                                        "similarity"
                                                    )
                                                ):.1%}"
                                        }
                                    )


                                peer_df = pd.DataFrame(peer_rows).drop_duplicates()
                                st.dataframe(
                                    peer_df,
                                    use_container_width=True,
                                    hide_index=True
                                )

                            else:

                                st.info(
                                    "No peer evidence available."
                                )


# ============================================================
# TAB 6 — GRAPH EXPLORER
# ============================================================

with tabs[5]:
    st.markdown('<div class="section-header">CRM Relationship Graph</div>', unsafe_allow_html=True)
    st.caption(
        "The overview combines every salesperson and their connected CRM entities. "
        "Dashed red links are inferred from shared domains, customers, or wins; they are not persisted Neo4j relationships."
    )

    if not neo4j_online:
        st.error("Neo4j is not currently available.")
    else:
        c1, c2, c3 = st.columns([1, 1.7, 0.8])
        with c1:
            entity_type = st.selectbox(
                "Entity Type", ["Employee", "Customer", "Opportunity", "Domain", "Product", "Stage"],
                key="graph_entity_type"
            )
        with c2:
            default_entity = "John" if entity_type == "Employee" else ""
            entity_name = st.text_input("Entity / ID", value=default_entity, key="graph_entity_name")
        with c3:
            depth = st.selectbox("Traversal Depth", [1, 2, 3], index=2, key="graph_depth_v2")

        show_team_graph = st.checkbox(
            "Show all salespeople and their connected entities", value=True,
            help="When enabled, the graph merges each employee's Neo4j neighborhood so John, Jake, Sarah, and other employees appear together."
        )
        explore = st.button("Explore Graph", type="primary", use_container_width=True)
        if "graph_loaded" not in st.session_state:
            st.session_state.graph_loaded = True
            explore = True

        # Rebuild the graph when the user explores, changes graph mode, or changes traversal settings.
        query_signature = (entity_type, entity_name.strip(), depth, show_team_graph)
        if explore or st.session_state.get("graph_query_signature") != query_signature:
            if not entity_name.strip() and not show_team_graph:
                st.warning("Enter an entity name or ID.")
            else:
                from urllib.parse import quote
                combined_nodes = {}
                combined_relationships = {}
                query_errors = []

                def merge_graph_response(response):
                    if not isinstance(response, dict):
                        return
                    for node in response.get("nodes", []) or []:
                        node_id = node.get("id")
                        if node_id is not None:
                            combined_nodes[str(node_id)] = node
                    for rel in response.get("relationships", []) or []:
                        source = rel.get("source")
                        target = rel.get("target")
                        if source is None or target is None:
                            continue
                        label = str(rel.get("label", rel.get("type", "RELATED_TO")))
                        key = (str(source), str(target), label)
                        combined_relationships[key] = {
                            **rel, "source": str(source), "target": str(target), "label": label
                        }

                with st.spinner("Building the combined sales-team graph from Neo4j..."):
                    if show_team_graph:
                        # /employees is the source of truth, so newly added employees are included automatically.
                        employee_rows = employees if isinstance(employees, list) else employees.get("employees", []) if isinstance(employees, dict) else []
                        employee_names = []
                        for employee in employee_rows:
                            if not isinstance(employee, dict):
                                continue
                            name = employee.get("name") or employee.get("employee_name")
                            if name and str(name).strip():
                                employee_names.append(str(name).strip())
                        # Keep the requested names available as a fallback if the employee endpoint is temporarily incomplete.
                        if not employee_names:
                            employee_names = ["John", "Jake", "Sarah"]
                        if entity_type == "Employee" and entity_name.strip() and entity_name.strip().lower() not in {n.lower() for n in employee_names}:
                            employee_names.append(entity_name.strip())
                        seen_names = set()
                        employee_names = [n for n in employee_names if not (n.lower() in seen_names or seen_names.add(n.lower()))]
                        for employee_name in employee_names:
                            response, error = api_get(
                                f"/graph?entity_type=Employee&entity_name={quote(employee_name)}&depth={depth}", timeout=30
                            )
                            if error:
                                query_errors.append(f"{employee_name}: {error}")
                            else:
                                merge_graph_response(response)
                        # For non-employee selections, add that selected entity's neighborhood to the team graph too.
                        if entity_type != "Employee" and entity_name.strip():
                            response, error = api_get(
                                f"/graph?entity_type={quote(entity_type)}&entity_name={quote(entity_name.strip())}&depth={depth}", timeout=30
                            )
                            if error:
                                query_errors.append(f"Selected entity: {error}")
                            else:
                                merge_graph_response(response)
                    else:
                        response, error = api_get(
                            f"/graph?entity_type={quote(entity_type)}&entity_name={quote(entity_name.strip())}&depth={depth}", timeout=30
                        )
                        if error:
                            query_errors.append(error)
                        else:
                            merge_graph_response(response)

                if combined_nodes:
                    st.session_state.graph_data = {
                        "nodes": list(combined_nodes.values()),
                        "relationships": list(combined_relationships.values()),
                        "selected_node_ids": [],
                    }
                    st.session_state.graph_query = (entity_type, entity_name.strip() or "All salespeople", depth)
                    st.session_state.graph_query_signature = query_signature
                    st.session_state.graph_query_errors = query_errors
                elif query_errors:
                    st.error("Could not load graph data. " + " | ".join(query_errors[:3]))
                else:
                    st.session_state.graph_data = {"nodes": [], "relationships": []}
                    st.session_state.graph_query = (entity_type, entity_name.strip() or "All salespeople", depth)
                    st.session_state.graph_query_signature = query_signature
                    st.session_state.graph_query_errors = query_errors

        graph = st.session_state.get("graph_data")
        if graph:
            nodes = graph.get("nodes", []) or []
            relationships = graph.get("relationships", []) or []
            node_by_id = {str(n.get("id")): n for n in nodes if n.get("id") is not None}
            entity_type_used, entity_name_used, depth_used = st.session_state.get(
                "graph_query", (entity_type, entity_name, depth)
            )

            actual_edges = []
            adjacency = {}
            for rel in relationships:
                source, target = str(rel.get("source")), str(rel.get("target"))
                if source not in node_by_id or target not in node_by_id:
                    continue
                label = str(rel.get("label", rel.get("type", "RELATED_TO")))
                actual_edges.append((source, target, label))
                adjacency.setdefault(source, []).append((target, label))
                adjacency.setdefault(target, []).append((source, label))

            def has_label(node, expected):
                labels = node.get("labels") or []
                if isinstance(labels, str):
                    labels = [labels]
                if not isinstance(labels, (list, tuple, set)):
                    return False
                return expected.lower() in [str(x).strip().lower() for x in labels if x not in (None, "")]

            employee_nodes = {nid: node for nid, node in node_by_id.items() if has_label(node, "Employee")}
            domain_nodes = {nid: node for nid, node in node_by_id.items() if has_label(node, "Domain")}
            customer_nodes = {nid: node for nid, node in node_by_id.items() if has_label(node, "Customer")}
            opportunity_nodes = {nid: node for nid, node in node_by_id.items() if has_label(node, "Opportunity")}

            employee_evidence = {eid: {"domains": set(), "customers": set(), "won_domains": set(), "won_opportunities": set()} for eid in employee_nodes}
            for employee_id in employee_nodes:
                for neighbor_id, rel_label in adjacency.get(employee_id, []):
                    if neighbor_id not in opportunity_nodes or rel_label.upper() != "OWNS":
                        continue
                    opportunity = opportunity_nodes[neighbor_id]
                    props = opportunity.get("properties", {}) or {}
                    outcome = str(props.get("outcome", "")).strip().lower()
                    # Use an explicit conditional instead of a bare conditional expression.
                    # Streamlit's magic renderer can display the expression result (None)
                    # for every non-winning opportunity, cluttering the page with "None".
                    if outcome == "won":
                        employee_evidence[employee_id]["won_opportunities"].add(neighbor_id)
                    for second_hop, second_rel in adjacency.get(neighbor_id, []):
                        if second_hop in domain_nodes and second_rel.upper() == "TARGETS":
                            employee_evidence[employee_id]["domains"].add(second_hop)
                            if outcome == "won":
                                employee_evidence[employee_id]["won_domains"].add(second_hop)
                        if second_hop in customer_nodes and second_rel.upper() in {"FOR_CUSTOMER", "WITH"}:
                            employee_evidence[employee_id]["customers"].add(second_hop)

            # Domain-to-domain semantic similarity edges already present in the graph.
            similar_domain_pairs = set()
            for source, target, rel_label in actual_edges:
                if rel_label.upper() == "SIMILAR_TO" and source in domain_nodes and target in domain_nodes:
                    similar_domain_pairs.add((source, target))
                    similar_domain_pairs.add((target, source))

            inferred_employee_edges = []
            employee_ids = sorted(employee_nodes, key=lambda eid: node_display_name(employee_nodes[eid]).lower())
            for i, first_id in enumerate(employee_ids):
                for second_id in employee_ids[i + 1:]:
                    a, b = employee_evidence[first_id], employee_evidence[second_id]
                    shared_domains = a["domains"] & b["domains"]
                    shared_customers = a["customers"] & b["customers"]
                    shared_won_domains = a["won_domains"] & b["won_domains"]
                    related_domain_pairs = [
                        (domain_a, domain_b)
                        for domain_a in a["domains"]
                        for domain_b in b["domains"]
                        if (domain_a, domain_b) in similar_domain_pairs
                    ]
                    evidence = []
                    if shared_domains:
                        evidence.extend(f"Shared domain: {node_display_name(domain_nodes[d])}" for d in sorted(shared_domains))
                    if shared_customers:
                        evidence.extend(f"Shared customer: {node_display_name(customer_nodes[c])}" for c in sorted(shared_customers))
                    if shared_won_domains:
                        evidence.extend(f"Both have wins in: {node_display_name(domain_nodes[d])}" for d in sorted(shared_won_domains))
                    if related_domain_pairs:
                        evidence.extend(
                            f"Similar domains: {node_display_name(domain_nodes[domain_a])} ↔ {node_display_name(domain_nodes[domain_b])}"
                            for domain_a, domain_b in related_domain_pairs
                        )
                    if evidence:
                        inferred_employee_edges.append((first_id, second_id, sorted(set(evidence))))

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Graph nodes", len(nodes))
            m2.metric("Neo4j relationships", len(actual_edges))
            m3.metric("Salespeople in graph", len(employee_nodes))
            m4.metric("Employee connections", len(inferred_employee_edges))
            st.caption(f"Graph scope: {'All salespeople + connected entities' if show_team_graph else 'Selected entity neighborhood'} · depth {depth_used}")

            if st.session_state.get("graph_query_errors"):
                with st.expander("Some employee graph queries could not be loaded"):
                    for error in st.session_state.graph_query_errors:
                        st.write(f"- {error}")

            if not nodes:
                st.info("No graph nodes were returned. Try a different entity or traversal depth.")
            else:
                show_all_labels = st.checkbox("Show labels for every node", value=False, key="graph_show_all_labels")
                type_order = ["Employee", "Opportunity", "Customer", "Domain", "Product", "Stage", "Interaction", "Industry"]
                grouped = {}
                for node in nodes:
                    grouped.setdefault(node_label(node), []).append(node)

                # Employees form the central ring; related entities occupy outer rings by type.
                positions = {}
                for label_index, label in enumerate(type_order + [x for x in grouped if x not in type_order]):
                    group = grouped.get(label, [])
                    if not group:
                        continue
                    n_group = len(group)
                    if label == "Employee":
                        ring = 2.3
                    else:
                        ring = 5.0 + max(0, type_order.index(label) if label in type_order else label_index) * 1.7
                    # Stable ordering by display name keeps the graph from reshuffling unnecessarily.
                    group = sorted(group, key=lambda n: node_display_name(n).lower())
                    for idx, node in enumerate(group):
                        angle = (2 * np.pi * idx / max(1, n_group)) + (label_index * 0.19)
                        positions[str(node["id"])] = (ring * np.cos(angle), ring * np.sin(angle))

                fig = go.Figure()
                edge_x, edge_y = [], []
                for source, target, label in actual_edges:
                    if source not in positions or target not in positions:
                        continue
                    x0, y0 = positions[source]; x1, y1 = positions[target]
                    edge_x.extend([x0, x1, None]); edge_y.extend([y0, y1, None])
                if edge_x:
                    fig.add_trace(go.Scatter(
                        x=edge_x, y=edge_y, mode="lines", name="Neo4j relationship",
                        line=dict(width=1, color="rgba(110,125,150,0.38)"), hoverinfo="skip", showlegend=True,
                    ))

                inferred_x, inferred_y = [], []
                inferred_hover = []
                for first_id, second_id, evidence in inferred_employee_edges:
                    if first_id not in positions or second_id not in positions:
                        continue
                    x0, y0 = positions[first_id]; x1, y1 = positions[second_id]
                    inferred_x.extend([x0, x1, None]); inferred_y.extend([y0, y1, None])
                    inferred_hover.append(f"{node_display_name(employee_nodes[first_id])} ↔ {node_display_name(employee_nodes[second_id])}: " + "; ".join(evidence))
                if inferred_x:
                    fig.add_trace(go.Scatter(
                        x=inferred_x, y=inferred_y, mode="lines", name="Employee-to-employee evidence",
                        line=dict(width=2.5, color="rgba(220,55,75,0.85)", dash="dash"), hoverinfo="skip", showlegend=True,
                    ))

                palette = {
                    "Employee": "#F4A6A6", "Opportunity": "#FFD166", "Domain": "#F08C00",
                    "Customer": "#7950B2", "Product": "#FA5252", "Stage": "#20A39E",
                    "Interaction": "#69DB7C", "Industry": "#748FFC",
                }
                selected_ids = {str(x) for x in graph.get("selected_node_ids", [])}
                for label, group in grouped.items():
                    group = sorted(group, key=lambda n: node_display_name(n).lower())
                    ids = [str(n["id"]) for n in group]
                    xs = [positions[nid][0] for nid in ids]
                    ys = [positions[nid][1] for nid in ids]
                    display_names = [node_display_name(n) for n in group]
                    texts = [name if show_all_labels or label == "Employee" or str(n.get("id")) in selected_ids else "" for n, name in zip(group, display_names)]
                    hover_values = []
                    for node in group:
                        props = node.get("properties", {}) or {}
                        details = [f"<b>{node_display_name(node)}</b>", f"Type: {label}"]
                        details.extend(f"{k}: {v}" for k, v in props.items() if v is not None)
                        hover_values.append("<br>".join(details))
                    fig.add_trace(go.Scatter(
                        x=xs, y=ys, mode="markers+text", text=texts, textposition="top center",
                        textfont=dict(size=11 if label == "Employee" else 9), hovertext=hover_values,
                        hoverinfo="text", name=label,
                        marker=dict(size=29 if label == "Employee" else 15, color=palette.get(label, "#748FFC"),
                                    line=dict(width=2 if label == "Employee" else 1, color="white")),
                    ))

                fig.update_layout(
                    height=850, showlegend=True, hovermode="closest", plot_bgcolor="white", paper_bgcolor="white",
                    margin=dict(l=20, r=20, t=25, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "scrollZoom": True})

                st.markdown("#### Employee Connections")
                if inferred_employee_edges:
                    connection_rows = []
                    for first_id, second_id, evidence in inferred_employee_edges:
                        connection_rows.append({
                            "Employee": node_display_name(employee_nodes[first_id]),
                            "Connected employee": node_display_name(employee_nodes[second_id]),
                            "Connection evidence": "; ".join(evidence),
                        })
                    st.dataframe(pd.DataFrame(connection_rows).drop_duplicates(), use_container_width=True, hide_index=True, height=220)
                else:
                    st.info("No shared domain, customer, or shared-win evidence was found between the employees in this graph. The employees and their actual Neo4j entity relationships are still shown above.")

                with st.expander("Inspect a graph entity"):
                    node_options = [f"{node_label(node)} — {node_display_name(node)} [{node.get('id')}]" for node in nodes]
                    selected_node_option = st.selectbox("Select a node", node_options, key="selected_graph_node")
                    selected_node = nodes[node_options.index(selected_node_option)]
                    st.write(f"**Type:** {node_label(selected_node)} · **Node ID:** `{selected_node.get('id')}`")
                    properties = selected_node.get("properties", {}) or {}
                    if properties:
                        st.dataframe(pd.DataFrame([{"Property": key, "Value": value} for key, value in properties.items()]), use_container_width=True, hide_index=True)
                    else:
                        st.info("No properties available.")

                with st.expander("Inspect Neo4j relationships"):
                    relationship_rows = [{
                        "Source type": node_label(node_by_id[source]), "Source": node_display_name(node_by_id[source]),
                        "Relationship": label, "Target type": node_label(node_by_id[target]), "Target": node_display_name(node_by_id[target]),
                    } for source, target, label in actual_edges]
                    if relationship_rows:
                        st.dataframe(pd.DataFrame(relationship_rows).drop_duplicates(), use_container_width=True, hide_index=True, height=320)
                    else:
                        st.info("No relationships found.")
        else:
            st.info("Click **Explore Graph** to load the graph.")


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CRM Analytics Engine • Neo4j + FastAPI + Streamlit "
    "• Graph Recommendation POC"
)
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

    .stApp {
        background: #f5f7fb;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-left: 2.5rem;
        padding-right: 2.5rem;
        max-width: 1600px;
    }

    section[data-testid="stSidebar"] {
        background: #111827;
        border-right: 1px solid #1f2937;
    }

    section[data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

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

    .status-online {
        color: #16a34a;
        font-weight: 600;
    }

    .status-offline {
        color: #dc2626;
        font-weight: 600;
    }

    .stButton > button {
        border-radius: 7px;
        font-weight: 600;
    }

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
    """Safe GET request to FastAPI."""

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


def api_post(endpoint, payload=None, timeout=15):
    """Safe POST request to FastAPI."""

    try:
        if payload is None:
            payload = {}

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

        if value not in [None, ""]:
            return str(value)

    return str(
        node.get(
            "id",
            "Unknown"
        )
    )


def node_label(node):

    labels = node.get(
        "labels",
        []
    )

    if labels:
        return labels[0]

    return "Node"


def normalize_employees(response):
    """
    Handles both:

    [
        {"id": "...", "name": "..."}
    ]

    and:

    {
        "employees": [
            {"id": "...", "name": "..."}
        ]
    }
    """

    if isinstance(response, list):
        return response

    if isinstance(response, dict):
        employees = response.get("employees", [])

        if isinstance(employees, list):
            return employees

    return []


def get_employee_name(employee):
    return (
        employee.get("name")
        or employee.get("employee_name")
        or employee.get("id")
        or "Unknown"
    )


def get_employee_id(employee):
    return (
        employee.get("id")
        or employee.get("employee_id")
    )


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
        <div style="font-size:24px;font-weight:700;">
            ◈ CRM Analytics
        </div>

        <div style="font-size:12px;color:#9ca3af;margin-top:4px;">
            Graph Intelligence Platform
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### Platform")

    if neo4j_online:

        st.markdown(
            '<span class="status-online">● Neo4j Online</span>',
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            '<span class="status-offline">● Neo4j Offline</span>',
            unsafe_allow_html=True
        )

    st.caption(
        f"API: {API}"
    )

    st.divider()

    st.markdown("### Architecture")

    st.caption("Graph Database")
    st.write("Neo4j")

    st.caption("API Layer")
    st.write("FastAPI")

    st.caption("Analytics UI")
    st.write("Streamlit")

    st.caption("Recommendation Engine")
    st.write("Graph + Weighted Scoring")

    st.divider()

    st.markdown("### Recommendation Model")

    st.caption("Domain Similarity")
    st.write("50%")

    st.caption("Peer Success")
    st.write("30%")

    st.caption("Historical Performance")
    st.write("20%")


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

employees_response, employees_error = api_get(
    "/employees",
    timeout=10
)

employees = normalize_employees(
    employees_response
)


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
            get_employee_name(employee):
                get_employee_id(employee)
            for employee in employees
            if get_employee_id(employee)
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

            performance = performance or {}

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
                        performance.get(
                            "total_opportunities",
                            0
                        )
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

            st.markdown(
                "#### Performance Details"
            )

            st.json(
                performance
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
            get_employee_name(employee):
                get_employee_id(employee)
            for employee in employees
            if get_employee_id(employee)
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

            result = result or {}

            recommendations = result.get(
                "recommendations",
                []
            )

            if not recommendations:

                st.info(
                    "No domain recommendations available."
                )

            else:

                for idx, rec in enumerate(
                    recommendations,
                    1
                ):

                    score = safe_float(
                        rec.get("score")
                    )

                    st.markdown(
                        f"""
                        <div class="recommendation-card">

                            <div class="recommendation-rank">
                                #{idx}
                            </div>

                            <div class="recommendation-name">
                                {rec.get("domain", "Unknown")}
                            </div>

                            <div style="margin-top:8px;">
                                Recommendation confidence:
                                <b>{score:.0%}</b>
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    st.progress(
                        min(
                            max(
                                score,
                                0
                            ),
                            1
                        )
                    )

                    st.write(
                        f"Source domain: "
                        f"**{rec.get('source_domain', 'Unknown')}**"
                    )

                    reasons = rec.get(
                        "reason",
                        []
                    )

                    if reasons:

                        st.write(
                            "**Why this domain?**"
                        )

                        for reason in reasons:

                            st.markdown(
                                f"""
                                <div class="reason-card">
                                    ✓ {reason}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                    st.divider()


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

    with st.form("create_opportunity_form"):

        left, right = st.columns(2)

        # ----------------------------------------------------
        # LEFT
        # ----------------------------------------------------

        with left:

            opportunity_name = st.text_input(
                "Opportunity Name",
                placeholder="e.g. Healthcare Payments Platform",
                key="create_opportunity_name"
            )

            customer_name = st.text_input(
                "Customer",
                placeholder="e.g. HealthPay Technologies",
                key="create_customer_name"
            )

            domain_name = st.text_input(
                "Business Domain",
                placeholder="e.g. Healthcare Payments",
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

                employee_name = get_employee_name(
                    employee
                )

                employee_id = get_employee_id(
                    employee
                )

                if employee_id:

                    salesperson_options[
                        employee_name
                    ] = employee_id

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

            clean_opportunity_name = (
                opportunity_name.strip()
            )

            clean_customer_name = (
                customer_name.strip()
            )

            clean_domain_name = (
                domain_name.strip()
            )

            payload = {

                "name":
                    clean_opportunity_name,

                "customer_name":
                    clean_customer_name,

                "domain":
                    clean_domain_name,

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

            st.markdown(
                "### Step 1 — Creating Opportunity"
            )

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

                created = created or {}

                opportunity = created.get(
                    "opportunity",
                    created
                )

                opportunity_id = (
                    opportunity.get("opportunity_id")
                    or opportunity.get("id")
                )

                if not opportunity_id:

                    st.error(
                        "Opportunity was created but the API "
                        "did not return an opportunity ID."
                    )

                    st.json(created)

                else:

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
                                clean_customer_name
                            )
                        )

                    with c3:

                        st.metric(
                            "Domain",
                            opportunity.get(
                                "domain",
                                clean_domain_name
                            )
                        )

                    with c4:

                        st.metric(
                            "Value",
                            format_currency(
                                opportunity.get(
                                    "opportunity_value",
                                    opportunity.get(
                                        "value",
                                        opportunity_value
                                    )
                                )
                            )
                        )

                    st.divider()

                    # ------------------------------------------------
                    # STEP 2 — DOMAIN SIMILARITY
                    # ------------------------------------------------

                    st.markdown(
                        "### Step 2 — Domain Intelligence"
                    )

                    st.caption(
                        "The new domain is passed through the semantic "
                        "similarity engine. Existing domains are compared "
                        "using embeddings and relevant SIMILAR_TO "
                        "relationships are created in Neo4j."
                    )

                    with st.spinner(
                        "Calculating domain similarity..."
                    ):

                        # IMPORTANT:
                        # This is POST /domains/{domain}/similarity
                        # NOT /domains/{domain}/similar
                        similarity_result, similarity_error = api_post(
                            f"/domains/{clean_domain_name}/similarity",
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

                        similarity_result = (
                            similarity_result or {}
                        )

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
                                                "source",
                                                relationship.get(
                                                    "source_domain",
                                                    ""
                                                )
                                            ),

                                        "Target Domain":
                                            relationship.get(
                                                "target",
                                                relationship.get(
                                                    "target_domain",
                                                    ""
                                                )
                                            ),

                                        "Similarity":
                                            f"{safe_float(
                                                relationship.get(
                                                    "score",
                                                    relationship.get(
                                                        "similarity",
                                                        0
                                                    )
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
                        # SHOW EXISTING SIMILAR DOMAINS
                        # ------------------------------------------------

                        similar_domains, similar_error = api_get(
                            f"/domains/{clean_domain_name}/similar",
                            timeout=20
                        )

                        if not similar_error and similar_domains:

                            similar_list = (
                                similar_domains.get(
                                    "similar_domains",
                                    []
                                )
                            )

                            if similar_list:

                                st.markdown(
                                    "#### Similar Domains in Neo4j"
                                )

                                similar_rows = []

                                for item in similar_list:

                                    if isinstance(item, dict):

                                        similar_rows.append(
                                            {
                                                "Domain":
                                                    item.get(
                                                        "domain",
                                                        item.get(
                                                            "name",
                                                            item.get(
                                                                "similar_domain",
                                                                ""
                                                            )
                                                        )
                                                    ),

                                                "Similarity":
                                                    f"{safe_float(
                                                        item.get(
                                                            "score",
                                                            item.get(
                                                                "similarity",
                                                                0
                                                            )
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

                    # ------------------------------------------------
                    # STEP 3 — SALESPERSON RECOMMENDATION
                    # ------------------------------------------------

                    if selected_salesperson == "Auto Recommend":

                        st.divider()

                        st.markdown(
                            "### Step 3 — Salesperson Recommendation"
                        )

                        st.caption(
                            "Salespeople are ranked using:"
                        )

                        st.info(
                            "50% Domain Similarity + "
                            "30% Peer Success + "
                            "20% Historical Performance"
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
                                "Opportunity was created successfully, "
                                "but salesperson recommendation failed."
                            )

                            st.code(
                                ranking_error
                            )

                        else:

                            ranking = ranking or {}

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
                                        "probability_percent"
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
                                # SCORE CALCULATION
                                # ------------------------------------

                                calculated_score = (
                                    0.50 * safe_float(
                                        top.get(
                                            "domain_similarity"
                                        )
                                    )
                                    +
                                    0.30 * safe_float(
                                        top.get(
                                            "peer_success"
                                        )
                                    )
                                    +
                                    0.20 * safe_float(
                                        top.get(
                                            "historical_performance"
                                        )
                                    )
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
                                    f"Final graph recommendation score: "
                                    f"**{calculated_score:.1%}**"
                                )

                                # ------------------------------------
                                # RANKING TABLE
                                # ------------------------------------

                                st.markdown(
                                    "#### Salesperson Ranking"
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

                                            "Score":
                                                f"{safe_float(
                                                    salesperson.get(
                                                        "probability_percent"
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

                                st.markdown(
                                    "#### Why was this salesperson recommended?"
                                )

                                reasons = top.get(
                                    "reasons",
                                    []
                                )

                                if reasons:

                                    for reason in reasons:

                                        st.markdown(
                                            f"""
                                            <div class="reason-card">
                                                ✓ {reason}
                                            </div>
                                            """,
                                            unsafe_allow_html=True
                                        )

                                # ------------------------------------
                                # DOMAIN EVIDENCE
                                # ------------------------------------

                                domain_evidence = (
                                    top.get(
                                        "domain_evidence",
                                        []
                                    )
                                    or []
                                )

                                if domain_evidence:

                                    st.markdown(
                                        "#### Domain Evidence"
                                    )

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

                                    st.dataframe(
                                        pd.DataFrame(
                                            evidence_rows
                                        ),
                                        use_container_width=True,
                                        hide_index=True
                                    )

                                # ------------------------------------
                                # PEER EVIDENCE
                                # ------------------------------------

                                peer_evidence = (
                                    top.get(
                                        "peer_evidence",
                                        []
                                    )
                                    or []
                                )

                                if peer_evidence:

                                    st.markdown(
                                        "#### Peer Evidence"
                                    )

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

                                    st.dataframe(
                                        pd.DataFrame(
                                            peer_rows
                                        ),
                                        use_container_width=True,
                                        hide_index=True
                                    )

                            else:

                                st.info(
                                    "No salesperson recommendations "
                                    "were generated."
                                )

                    else:

                        st.divider()

                        st.success(
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
        "Select an open opportunity to see conversion probability "
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

            st.markdown(
                f"""
                <div class="graph-info">

                    <h3>
                        {row.get("opportunity_name", selected_opp)}
                    </h3>

                    <b>Opportunity ID:</b>
                    {selected_opp}

                    <br><br>

                    <b>Customer:</b>
                    {row.get("customer_name", "Unknown")}

                    <br>

                    <b>Domain:</b>
                    {row.get("domain", "Unknown")}

                </div>
                """,
                unsafe_allow_html=True
            )

            # ------------------------------------------------
            # CONVERSION PREDICTION
            # ------------------------------------------------

            prediction, prediction_error = api_get(
                f"/opportunities/{selected_opp}/prediction",
                timeout=15
            )

            if prediction_error:

                st.warning(
                    f"Conversion prediction unavailable: "
                    f"{prediction_error}"
                )

            else:

                prediction = prediction or {}

                probability = safe_float(
                    prediction.get(
                        "probability_percent"
                    )
                )

                p1, p2, p3 = st.columns(3)

                with p1:

                    st.metric(
                        "Probability of Conversion",
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

                ranking = ranking or {}

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

                    top = salespeople[0]

                    top_score = safe_float(
                        top.get(
                            "probability_percent"
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
                        f"Final graph recommendation score: "
                        f"**{calculated_score:.1%}**"
                    )

                    # -----------------------------------------
                    # EXPLAINABILITY
                    # -----------------------------------------

                    st.markdown(
                        "##### Why was this salesperson recommended?"
                    )

                    reasons = top.get(
                        "reasons",
                        []
                    )

                    if reasons:

                        for reason in reasons:

                            st.markdown(
                                f"""
                                <div class="reason-card">
                                    ✓ {reason}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

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

                                "Conversion Score":
                                    f"{safe_float(
                                        salesperson.get(
                                            "probability_percent"
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
                    # DETAILED EVIDENCE
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

                                st.dataframe(
                                    pd.DataFrame(
                                        evidence_rows
                                    ),
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

                                st.dataframe(
                                    pd.DataFrame(
                                        peer_rows
                                    ),
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

    st.markdown(
        '<div class="section-header">Graph Explorer</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Explore the actual Neo4j knowledge graph behind "
        "CRM recommendations and analytics."
    )

    if not neo4j_online:

        st.error(
            "Neo4j is not currently available."
        )

    else:

        # ----------------------------------------------------
        # CONTROLS
        # ----------------------------------------------------

        c1, c2, c3 = st.columns(
            [1, 2, 1]
        )

        with c1:

            entity_type = st.selectbox(
                "Entity Type",
                [
                    "Employee",
                    "Customer",
                    "Opportunity",
                    "Domain",
                    "Product",
                    "Stage",
                ],
                key="graph_entity_type"
            )

        with c2:

            default_entity = (
                "John"
                if entity_type == "Employee"
                else ""
            )

            entity_name = st.text_input(
                "Entity / ID",
                value=default_entity,
                key="graph_entity_name"
            )

        with c3:

            depth = st.selectbox(
                "Traversal Depth",
                [1, 2, 3],
                index=1,
                key="graph_depth"
            )

        explore = st.button(
            "Explore Graph",
            type="primary",
            use_container_width=True
        )

        if (
            "graph_loaded"
            not in st.session_state
        ):

            st.session_state.graph_loaded = True
            explore = True

        if explore:

            if not entity_name.strip():

                st.warning(
                    "Enter an entity name or ID."
                )

            else:

                with st.spinner(
                    "Querying Neo4j graph..."
                ):

                    graph, error = api_get(
                        "/graph"
                        f"?entity_type={entity_type}"
                        f"&entity_name={entity_name}"
                        f"&depth={depth}",
                        timeout=30
                    )

                if error:

                    st.error(error)

                elif graph:

                    st.session_state.graph_data = graph

        graph = st.session_state.get(
            "graph_data"
        )

        if graph:

            nodes = graph.get(
                "nodes",
                []
            )

            relationships = graph.get(
                "relationships",
                []
            )

            st.markdown(
                f"""
                <div class="graph-info">

                    <b>Graph:</b>
                    {entity_type} → {entity_name}

                    &nbsp;&nbsp;|&nbsp;&nbsp;

                    <b>Nodes:</b>
                    {len(nodes)}

                    &nbsp;&nbsp;|&nbsp;&nbsp;

                    <b>Relationships:</b>
                    {len(relationships)}

                </div>
                """,
                unsafe_allow_html=True
            )

            # ------------------------------------------------
            # NODE POSITIONS
            # ------------------------------------------------

            node_ids = [
                node["id"]
                for node in nodes
            ]

            node_index = {
                node_id: idx
                for idx, node_id
                in enumerate(node_ids)
            }

            count = len(nodes)

            if count > 0:

                angles = np.linspace(
                    0,
                    2 * np.pi,
                    count,
                    endpoint=False
                )

                radius = 10

                positions = {

                    node["id"]: (

                        radius * np.cos(
                            angles[idx]
                        ),

                        radius * np.sin(
                            angles[idx]
                        )
                    )

                    for idx, node
                    in enumerate(nodes)
                }

            else:

                positions = {}

            # ------------------------------------------------
            # GRAPH FIGURE
            # ------------------------------------------------

            fig = go.Figure()

            # ------------------------------------------------
            # EDGES
            # ------------------------------------------------

            for relationship in relationships:

                source = relationship.get(
                    "source"
                )

                target = relationship.get(
                    "target"
                )

                if (
                    source not in positions
                    or target not in positions
                ):

                    continue

                x0, y0 = positions[source]
                x1, y1 = positions[target]

                fig.add_trace(
                    go.Scatter(
                        x=[x0, x1],
                        y=[y0, y1],
                        mode="lines",
                        line=dict(
                            width=1
                        ),
                        hoverinfo="none",
                        showlegend=False,
                    )
                )

                xm = (
                    x0 + x1
                ) / 2

                ym = (
                    y0 + y1
                ) / 2

                fig.add_annotation(
                    x=xm,
                    y=ym,
                    text=relationship.get(
                        "label",
                        ""
                    ),
                    showarrow=False,
                    font=dict(
                        size=9
                    )
                )

            # ------------------------------------------------
            # NODE GROUPS
            # ------------------------------------------------

            for label in set(
                node_label(node)
                for node in nodes
            ):

                group = [
                    node
                    for node in nodes
                    if node_label(node) == label
                ]

                x_values = [
                    positions[
                        node["id"]
                    ][0]
                    for node in group
                ]

                y_values = [
                    positions[
                        node["id"]
                    ][1]
                    for node in group
                ]

                text_values = [
                    node_display_name(node)
                    for node in group
                ]

                hover_values = []

                for node in group:

                    properties = node.get(
                        "properties",
                        {}
                    )

                    hover_text = (
                        f"<b>{node_display_name(node)}</b>"
                        f"<br>Type: {label}"
                    )

                    for key, value in properties.items():

                        if value is None:
                            continue

                        hover_text += (
                            f"<br>{key}: {value}"
                        )

                    hover_values.append(
                        hover_text
                    )

                fig.add_trace(
                    go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode="markers+text",
                        text=text_values,
                        textposition="top center",
                        hovertext=hover_values,
                        hoverinfo="text",
                        marker=dict(
                            size=24,
                            line=dict(
                                width=1
                            ),
                        ),
                        name=label,
                    )
                )

            fig.update_layout(
                height=700,
                showlegend=True,
                hovermode="closest",
                plot_bgcolor="white",
                paper_bgcolor="white",
                margin=dict(
                    l=20,
                    r=20,
                    t=20,
                    b=20,
                ),
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                ),
                yaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    showticklabels=False,
                    scaleanchor="x",
                    scaleratio=1,
                ),
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # ------------------------------------------------
            # NODE EXPLORER
            # ------------------------------------------------

            st.markdown(
                "#### Graph Entities"
            )

            node_names = [

                f"{node_label(node)} — "
                f"{node_display_name(node)}"

                for node in nodes

            ]

            if node_names:

                selected_node_name = st.selectbox(
                    "Select a node to inspect",
                    node_names,
                    key="selected_graph_node"
                )

                selected_index = node_names.index(
                    selected_node_name
                )

                selected_node = nodes[
                    selected_index
                ]

                left, right = st.columns(
                    [1, 2]
                )

                with left:

                    st.markdown(
                        f"""
                        **Type**

                        `{node_label(selected_node)}`
                        """
                    )

                    st.markdown(
                        f"""
                        **Node ID**

                        `{selected_node.get("id")}`
                        """
                    )

                with right:

                    st.markdown(
                        "**Properties**"
                    )

                    properties = selected_node.get(
                        "properties",
                        {}
                    )

                    if properties:

                        property_df = pd.DataFrame(
                            [
                                {
                                    "Property": key,
                                    "Value": value
                                }

                                for key, value
                                in properties.items()
                            ]
                        )

                        st.dataframe(
                            property_df,
                            use_container_width=True,
                            hide_index=True,
                        )

                    else:

                        st.info(
                            "No properties available."
                        )

            # ------------------------------------------------
            # RELATIONSHIPS
            # ------------------------------------------------

            st.markdown(
                "#### Relationships"
            )

            relationship_rows = []

            for relationship in relationships:

                source_node = next(
                    (
                        node
                        for node in nodes
                        if node["id"]
                        ==
                        relationship.get(
                            "source"
                        )
                    ),
                    None
                )

                target_node = next(
                    (
                        node
                        for node in nodes
                        if node["id"]
                        ==
                        relationship.get(
                            "target"
                        )
                    ),
                    None
                )

                if (
                    source_node is None
                    or target_node is None
                ):

                    continue

                relationship_rows.append(
                    {
                        "Source":
                            node_display_name(
                                source_node
                            ),

                        "Relationship":
                            relationship.get(
                                "label"
                            ),

                        "Target":
                            node_display_name(
                                target_node
                            ),
                    }
                )

            if relationship_rows:

                st.dataframe(
                    pd.DataFrame(
                        relationship_rows
                    ),
                    use_container_width=True,
                    hide_index=True,
                )

            else:

                st.info(
                    "No relationships found."
                )

        else:

            st.info(
                "Select an entity and click "
                "**Explore Graph**."
            )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "CRM Analytics Engine • Neo4j + FastAPI + Streamlit "
    "• Graph Recommendation POC"
)
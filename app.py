 # app.py

import streamlit as st
import pandas as pd
import altair as alt

# -----------------------------------
# 1. App Configuration & Title
# -----------------------------------
st.set_page_config(
    page_title="AI-Powered Claims Validator",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🚀 AI-Powered Claims Validation")

st.markdown(
    """
    This prototype **flags** potential coding errors (ICD-10/CPT mismatches) 
    and shows **mock AI suggestions** for correction. 
    Upload a CSV of fabricated claims and see real-time results.
    """
)

# -----------------------------------
# 2. File Upload Section
# -----------------------------------
st.sidebar.header("Upload Claims CSV")
uploaded_file = st.sidebar.file_uploader(
    "Choose a CSV file with columns: claim_id, diagnosis_codes, procedure_codes, provider_note, payer, denial_status",
    type=["csv"]
)

# If no file is uploaded, show a sample download link
if not uploaded_file:
    st.sidebar.info(
        "No file uploaded. You can download a "
        "sample CSV to try: [Download sample_claims.csv](data/sample_claims.csv)"
    )
    st.stop()  # Stop execution here until a file is provided

# Read uploaded CSV into DataFrame
df = pd.read_csv(uploaded_file)

# -----------------------------------
# 3. Basic Data Validation & Cleanup
# -----------------------------------
required_cols = [
    "claim_id", "diagnosis_codes", "procedure_codes", "provider_note", "payer", "denial_status"
]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"Missing required columns: {', '.join(missing_cols)}")
    st.stop()

# For demonstration, ensure diagnosis_codes/procedure_codes are strings
df["diagnosis_codes"] = df["diagnosis_codes"].astype(str)
df["procedure_codes"] = df["procedure_codes"].astype(str)

# -----------------------------------
# 4. Rule-Based Flagging Logic
# -----------------------------------
# A simple mapping of ICD-10 prefixes to valid CPT codes
valid_combos = {
    "M16": "27447",  # Hip arthroplasty
    "I10": "99213",  # Hypertension office visit
    "E11": "83036",  # Diabetes HbA1c
    "M17": "29881",  # Knee meniscectomy
    "I25": "99214",  # Cardiology follow-up
    "M54": "20550",  # Trigger point injection
    "J45": "94640",  # Nebulizer therapy
    "G43": "96372",  # Infusion therapy for headaches
    "E78": "80061",  # Lipid panel
}

def flag_invalid_combo(row):
    """
    Returns True if the combination of diagnosis and procedure looks invalid,
    False otherwise.
    """
    # Take the first 3 characters of diagnosis code
    diag_prefix = row["diagnosis_codes"][:3]
    proc = row["procedure_codes"]
    if diag_prefix in valid_combos:
        # If the procedure does NOT match the expected CPT, flag
        return proc != valid_combos[diag_prefix]
    else:
        # If the diagnosis prefix is not in our map, flag as potential risk
        return True

# Apply the flagging function to each row
df["flagged"] = df.apply(flag_invalid_combo, axis=1)

# -----------------------------------
# 5. Mock AI Suggestion Column
# -----------------------------------
def mock_ai_suggestion(row):
    """
    Returns a simple text suggestion for flagged claims;
    blank for unflagged.
    """
    if not row["flagged"]:
        return ""
    diag = row["diagnosis_codes"]
    proc = row["procedure_codes"]
    return (
        f"Check if CPT {proc} matches diagnosis {diag}. "
        "Consider adding a supporting diagnosis or correcting the code."
    )

df["ai_suggestion"] = df.apply(mock_ai_suggestion, axis=1)

# -----------------------------------
# 6. Summary Metrics & Filters
# -----------------------------------
total_claims = len(df)
flagged_count = df["flagged"].sum()
pct_flagged = round((flagged_count / total_claims) * 100, 1)

col1, col2, col3 = st.columns(3)
col1.metric("Total Claims", total_claims)
col2.metric("Flagged Claims", flagged_count, f"{pct_flagged}%")
col3.metric("Valid Claims", total_claims - flagged_count)

st.sidebar.header("Filter Options")
show_only_flagged = st.sidebar.checkbox("Show only flagged claims", value=False)
if show_only_flagged:
    display_df = df[df["flagged"] == True].copy()
else:
    display_df = df.copy()

# -----------------------------------
# 7. Interactive Table Display
# -----------------------------------
def highlight_flagged(val):
    """
    Return a CSS background color if flagged is True.
    """
    if val:
        return "background-color: #FFCCCC"  # Light red for flagged
    return ""

styled_df = (
    display_df.style
    .applymap(highlight_flagged, subset=["flagged"])
    .set_properties(subset=["ai_suggestion"], **{"width": "300px"})
)

st.subheader("Claims Data")
st.dataframe(styled_df, use_container_width=True)

# -----------------------------------
# 8. Visual Charts
# -----------------------------------
st.subheader("Flagged Claims by Payer")

# Aggregate flagged counts by payer
flagged_by_payer = (
    df[df["flagged"]]
    .groupby("payer")
    .size()
    .reset_index(name="count")
)

# If no flagged claims exist for some payer, ensure 0 is shown
all_payers = df["payer"].unique()
flagged_by_payer = flagged_by_payer.set_index("payer").reindex(all_payers, fill_value=0).reset_index()

chart = (
    alt.Chart(flagged_by_payer)
    .mark_bar(color="#E74C3C")  # Red bars
    .encode(
        x=alt.X("payer:N", title="Payer"),
        y=alt.Y("count:Q", title="Number of Flagged Claims"),
        tooltip=["payer", "count"]
    )
    .properties(width=600, height=300)
)
st.altair_chart(chart, use_container_width=True)

# -----------------------------------
# 9. Download Option
# -----------------------------------
st.subheader("Download Flagged Claims")
flagged_df = df[df["flagged"] == True].copy()
csv_flagged = flagged_df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="📥 Download Flagged Claims as CSV",
    data=csv_flagged,
    file_name="flagged_claims.csv",
    mime="text/csv"
)

st.markdown("---")
st.markdown(
    """
    **Notes:**  
    - “Flagged Claims” are those where our **rule engine** detected a possible ICD-10 / CPT mismatch.  
    - “AI Suggestion” is a **mock** text—demonstrating where a real LLM (e.g. GPT-4) would suggest corrections.  
    - In a full version, the AI could parse `provider_note` and return more precise recommendations.  
    """
)


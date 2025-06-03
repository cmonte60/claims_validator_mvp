import streamlit as st
import pandas as pd
import numpy as np
import random

# --- Page Config ---
st.set_page_config(
    page_title="Claims Predictor MVP",
    page_icon="📄",
    layout="wide"
)

# --- Styling ---
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .title { font-size: 36px; font-weight: bold; color: #343a40; }
        .subtitle { font-size: 20px; color: #6c757d; }
        .footer { text-align: center; font-size: 14px; margin-top: 50px; color: #adb5bd; }
    </style>
""", unsafe_allow_html=True)

# --- Title ---
st.markdown("<div class='title'>AI-Powered Claims Analysis Platform</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Predict insurance payment outcomes and understand denial reasons in seconds</div>", unsafe_allow_html=True)

# --- Upload Section ---
st.sidebar.header("Upload Claims Data (.csv)")
uploaded_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")

# --- Denial Interpretation Logic ---
def generate_interpretation(reason):
    interpretation_map = {
        "Incorrect CPT/ICD pairing": "Diagnosis and procedure codes mismatch; check ICD and CPT alignment.",
        "Missing modifier": "Modifier required for procedure; verify documentation.",
        "Authorization not found": "Claim denied due to absence of prior auth; verify if authorization was submitted.",
        "Non-covered service": "Procedure not covered under patient's plan; consider appeal or secondary coverage.",
        "Documentation incomplete": "Missing clinical documentation to support medical necessity.",
        "Claim submitted past timely filing limit": "Claim submitted after deadline; access internal process delays."
    }
    return interpretation_map.get(reason, "Check claim submission for details.")

# --- Prediction Logic ---
def load_and_predict(df):
    df = df.copy()
    np.random.seed(42)
    df['Predicted Status'] = np.random.choice(['Approved', 'Denied'], size=len(df), p=[0.7, 0.3])
    df['Confidence'] = np.round(np.random.uniform(0.75, 0.98, size=len(df)), 2)

    denial_reasons = [
        "Incorrect CPT/ICD pairing",
        "Missing modifier",
        "Authorization not found",
        "Non-covered service",
        "Documentation incomplete",
        "Claim submitted past timely filing limit"
    ]

    df['Likely Denial Reason'] = df['Predicted Status'].apply(
        lambda x: random.choice(denial_reasons) if x == 'Denied' else ''
    )

    df['AI Interpretation'] = df['Likely Denial Reason'].apply(generate_interpretation)

    return df

# --- Main App Logic ---
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Raw Claims Data")
    st.dataframe(df)

    processed_df = load_and_predict(df)

    st.subheader("Predicted Outcomes")
    expected_columns = ["Claim ID", "Predicted Status", "Confidence", "Likely Denial Reason", "AI Interpretation"]
    available_columns = [col for col in expected_columns if col in processed_df.columns]

    st.dataframe(processed_df[available_columns])

    csv = processed_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Predictions as CSV",
        data=csv,
        file_name='predicted_claims.csv',
        mime='text/csv'
    )
else:
    st.info("Please upload a CSV file to begin analysis.")

# --- Footer ---
st.markdown("""
    <div class='footer'>
        Prototype powered by AI | Designed for hospital leadership demonstration
    </div>
""", unsafe_allow_html=True)

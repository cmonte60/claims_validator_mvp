# app.py
import streamlit as st
import pandas as pd
import openai
import re

# --- Page Config ---
st.set_page_config(
    page_title="Claims Predictor MVP",
    layout="wide"
)

# --- Sidebar: API Key and File Upload ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
uploaded_file = st.sidebar.file_uploader("Upload Claims CSV", type="csv")

# --- Helper: Build Prompt ---
def build_prompt(row):
    return f"""
You are a medical coding AI assistant reviewing insurance claims.

Here is a claim record:
- Claim ID: {row['Claim ID']}
- Patient Age: {row['Patient Age']}
- Payer: {row['Payer']}
- CPT Code: {row['CPT Code']}
- ICD-10 Code: {row['ICD-10 Code']}
- Modifier: {row['Modifier']}
- Prior Authorization: {row['Prior Authorization']}
- Total Charges: ${row['Total Charges']}
- Days from Discharge to Submission: {row['Days from Discharge to Submission']}

<<<<<<< HEAD
Please answer in the format:
Status: Approved or Denied  
Confidence: X%  
Reason: [only if Denied OR Confidence < 90%]  
Suggestion: [only if Denied OR Confidence < 90%]

Be concise but clinical.
"""

# --- Helper: Parse GPT Output ---
def parse_response(text):
    result = {
        "Predicted Status": "",
        "Confidence": "",
        "Likely Denial Reason": "",
        "Suggested Fix": ""
    }
    lines = text.splitlines()
    for line in lines:
        if line.startswith("Status:"):
            result["Predicted Status"] = line.split(":", 1)[1].strip()
        elif line.startswith("Confidence:"):
            result["Confidence"] = line.split(":", 1)[1].strip()
        elif line.startswith("Reason:"):
            result["Likely Denial Reason"] = line.split(":", 1)[1].strip()
        elif line.startswith("Suggestion:"):
            result["Suggested Fix"] = line.split(":", 1)[1].strip()
    return result

# --- Main Processing Function ---
def analyze_claims(df, api_key):
    openai.api_key = api_key
    results = []
    with st.spinner("Analyzing claims using AI..."):
        for _, row in df.iterrows():
            prompt = build_prompt(row)
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are a helpful medical coding assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                reply = response["choices"][0]["message"]["content"]
                parsed = parse_response(reply)
                results.append(parsed)
            except Exception as e:
                results.append({
                    "Predicted Status": "Error",
                    "Confidence": "",
                    "Likely Denial Reason": str(e),
                    "Suggested Fix": "Check API or prompt"
                })
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)

# --- Main UI ---
st.title("AI-Powered Claims Review Platform")
st.caption("Demonstrate predictive denial analysis and real-time suggestions using GPT-4o")

if not api_key:
    st.warning("Please enter your OpenAI API key to begin.")
elif uploaded_file:
=======
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
>>>>>>> 09316c614c4c343983b41cd049cad079db4bc5d0
    df = pd.read_csv(uploaded_file)
    st.subheader("Raw Claims Data")
    st.dataframe(df)

    processed_df = analyze_claims(df, api_key)

<<<<<<< HEAD
    st.subheader("AI Feedback")
    st.dataframe(processed_df[[
        "Claim ID", "Predicted Status", "Confidence",
        "Likely Denial Reason", "Suggested Fix"
    ]])

    csv = processed_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Full Results", data=csv, file_name="ai_claims_results.csv", mime="text/csv")
=======
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
>>>>>>> 09316c614c4c343983b41cd049cad079db4bc5d0
else:
    st.info("Upload a claims file to start.")

# --- Footer ---
st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 13px;'>
        Prototype powered by GPT-4o | Designed for real-time claims prediction and denial mitigation
    </div>
""", unsafe_allow_html=True)


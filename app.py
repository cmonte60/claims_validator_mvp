# app.py
import streamlit as st
import pandas as pd
import asyncio
import httpx
import re
import openai

# --- Page Config ---
st.set_page_config(
    page_title="Claims Predictor MVP",
    layout="wide"
)
# --- Enable Text Wrapping in Data Table ---
st.markdown("""
    <style>
        /* Wrap long text in tables */
        .dataframe td {
            white-space: normal !important;
            word-wrap: break-word !important;
        }
        .stDataFrame tbody td {
            white-space: normal !important;
            word-wrap: break-word !important;
            max-width: 400px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar: API Key and File Upload ---
st.sidebar.header("Configuration")
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")
uploaded_file = st.sidebar.file_uploader("Upload Claims CSV", type="csv")

# --- Utility: Get best matching column name ---
def get_column(row, options):
    for col in options:
        if col in row.index:
            return col
    return options[0]  # default to first if none found

# --- Updated Prompt Builder ---
def build_prompt(row):
    patient_age = row.get(get_column(row, ['Patient Age', 'Age']), 'Unknown')
    patient_gender = row.get(get_column(row, ['Gender', 'Sex']), 'Unknown')
    procedure_code = row.get(get_column(row, ['Procedure Code', 'CPT']), 'Unknown')
    diagnosis_code = row.get(get_column(row, ['Diagnosis Code', 'ICD']), 'Unknown')
    payer = row.get(get_column(row, ['Payer', 'Insurance']), 'Unknown')
    total_charges = row.get(get_column(row, ['Total Charges', 'Charges']), 'Unknown')
    location = row.get(get_column(row, ['Service Location', 'Hospital', 'Facility']), 'Unknown')
    notes = row.get(get_column(row, ['Provider Notes', 'Notes', 'Justification']), '')

    return f"""
You are an expert in medical billing. Given the following patient claim information, predict whether this claim will be approved or denied, with a confidence score. If likely denied, explain the reason and give suggestions to increase approval likelihood.

Keep your response concise:
- Limit denial reasons to one short sentence or phrase
- Keep suggestions under 15 words and actionable

- Patient Age: {patient_age}
- Gender: {patient_gender}
- Procedure Code (CPT): {procedure_code}
- Diagnosis Code (ICD-10): {diagnosis_code}
- Payer: {payer}
- Total Charges: {total_charges}
- Location: {location}
- Provider Notes: {notes}

Respond in the following format:

Approval Prediction: [Approved/Denied]  
Confidence Score: [0.0 to 1.0]  
Reason for Denial (if applicable): [Concise phrase or one-sentence explanation]  
Suggested Fix (if applicable): [One short, actionable sentence under 15 words]
"""


# --- Response Parser ---
def parse_response(text):
    approved = re.search(r"Approval Prediction:\s*(Approved|Denied)", text, re.IGNORECASE)
    confidence = re.search(r"Confidence Score:\s*([0-9.]+)", text, re.IGNORECASE)
    reason = re.search(r"Reason for Denial.*?:\s*(.*)", text, re.IGNORECASE)
    suggestion = re.search(r"Suggested Fix.*?:\s*(.*)", text, re.IGNORECASE)

    status = approved.group(1).capitalize() if approved else "Unknown"
    conf_score = float(confidence.group(1)) if confidence else None

    denial_reason = reason.group(1).strip() if status == "Denied" and reason else ""
    suggestion_text = suggestion.group(1).strip() if status == "Denied" and suggestion else ""

    if status == "Approved" and conf_score and conf_score >= 0.90:
        denial_reason = ""
        suggestion_text = ""

    return {
        "Predicted Status": status,
        "Confidence": conf_score,
        "Likely Denial Reason": denial_reason,
        "Suggested Fix": suggestion_text
    }

# --- Async OpenAI Call ---
async def async_call_openai(prompt, api_key):
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        json_data = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a helpful medical coding assistant."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=json_data)
            reply = response.json()["choices"][0]["message"]["content"]
            return parse_response(reply)
    except Exception as e:
        return {
            "Predicted Status": "Error",
            "Confidence": "",
            "Likely Denial Reason": str(e),
            "Suggested Fix": "Check API or prompt"
        }

# --- Main Processing Function ---
def analyze_claims(df, api_key):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    prompts = [build_prompt(row) for _, row in df.iterrows()]
    tasks = [async_call_openai(prompt, api_key) for prompt in prompts]
    results = loop.run_until_complete(asyncio.gather(*tasks))
    return pd.concat([df.reset_index(drop=True), pd.DataFrame(results)], axis=1)

# --- Main UI ---
st.title("AI-Powered Claims Review Platform")
st.caption("Demonstrate predictive denial analysis and real-time suggestions using GPT-4o")

if not api_key:
    st.warning("Please enter your OpenAI API key to begin.")
elif uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Raw Claims Data")
    st.dataframe(df)

    processed_df = analyze_claims(df, api_key)

    st.subheader("AI Feedback")
    st.data_editor(
        processed_df[[
            "Claim ID", "Predicted Status", "Confidence",
            "Likely Denial Reason", "Suggested Fix"
        ]],
        column_config={
            "Likely Denial Reason": st.column_config.TextColumn(width="medium"),
            "Suggested Fix": st.column_config.TextColumn(width="medium")
        },
        hide_index=True,
        use_container_width=True,
        disabled=True  # Makes it read-only like st.dataframe
    )
    use_container_width=True,
        column_config={
            "Likely Denial Reason": st.column_config.TextColumn(
                "Likely Denial Reason", width="medium"
            ),
            "Suggested Fix": st.column_config.TextColumn(
                "Suggested Fix", width="medium"
            )
        },
        hide_index=True
    )

    csv = processed_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Full Results", data=csv, file_name="ai_claims_results.csv", mime="text/csv")

else:
    st.info("Upload a claims file to start.")


# --- Footer ---
st.markdown("""
    <hr>
    <div style='text-align: center; font-size: 13px;'>
        Prototype powered by GPT-4o | Designed for real-time claims prediction and denial mitigation
    </div>
""", unsafe_allow_html=True)

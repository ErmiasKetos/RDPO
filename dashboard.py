import streamlit as st
import pandas as pd
from google_sheets import get_google_sheets_client

st.title("📊 Purchase Order Dashboard")

# Get Google Sheets Data
client = get_google_sheets_client()
sheet = client.open_by_key("YOUR_SHEET_ID").worksheet("purchase_summary")
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Display Metrics
total_requests = df.shape[0]
pending_requests = df[df["Urgency"] == "Urgent"].shape[0]

st.metric(label="Total Purchase Orders", value=total_requests)
st.metric(label="Urgent Requests", value=pending_requests)

# Monthly Summary
df["Request Date and Time"] = pd.to_datetime(df["Request Date and Time"])
df["Month"] = df["Request Date and Time"].dt.strftime("%Y-%m")

monthly_summary = df.groupby("Month").size().reset_index(name="Requests")
st.line_chart(monthly_summary.set_index("Month"))

# Top Requesters
top_requesters = df["Requester"].value_counts().head(5)
st.bar_chart(top_requesters)

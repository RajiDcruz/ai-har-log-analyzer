import streamlit as st
import json
import pandas as pd
import matplotlib.pyplot as plt
from urllib.parse import urlparse
from openai import OpenAI
import os

# 🔑 API Key (use env variable)
client = OpenAI(api_key="you API key")

st.set_page_config(page_title="AI HAR Analyzer Pro", layout="wide")

st.title("🚀 AI HAR Log Analyzer Pro")
st.write("Analyze HAR files with AI-powered insights, charts, and diagnostics.")

uploaded_file = st.file_uploader("Upload HAR File", type=["har"])


# 🔍 Analyze HAR
def analyze_har(data):
    entries = data['log']['entries']
    records = []

    for entry in entries:
        url = entry['request']['url']
        status = entry['response']['status']
        time = entry['time']
        domain = urlparse(url).netloc

        records.append({
            "url": url,
            "status": status,
            "time": time,
            "domain": domain
        })

    df = pd.DataFrame(records)

    errors = df[df["status"] >= 400]
    slow = df[df["time"] > 1000]

    return df, errors, slow


# 🎯 Top Issues
def get_top_issues(errors, slow):
    issues = []

    if not errors.empty:
        top_error = errors.iloc[0]
        issues.append(f"High error detected: {top_error['status']} on {top_error['domain']}")

    if not slow.empty:
        top_slow = slow.iloc[0]
        issues.append(f"Slow API: {top_slow['time']} ms on {top_slow['domain']}")

    if not issues:
        issues.append("No major issues detected")

    return issues[:3]


# 🧠 AI Analysis (with fallback)
def get_ai_analysis(errors, slow):
    try:
        prompt = f"""
        Analyze HAR log issues:

        Errors:
        {errors[['url','status']].head(5).to_dict()}

        Slow Requests:
        {slow[['url','time']].head(5).to_dict()}

        Provide:
        - Summary
        - Root causes
        - Suggested fixes
        """

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"""
⚠️ AI Insights unavailable (API quota or key issue)

Fallback Analysis:
- Total Errors: {len(errors)}
- Total Slow Requests: {len(slow)}

Possible Causes:
- Backend API failures
- Network latency
- Authentication/session issues

Suggested Fix:
- Check failed API endpoints
- Validate backend logs
- Optimize slow APIs
"""


# 🚀 MAIN APP
if uploaded_file:
    data = json.load(uploaded_file)

    df, errors, slow = analyze_har(data)

    # 📊 Metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Requests", len(df))
    col2.metric("Errors", len(errors))
    col3.metric("Slow Requests", len(slow))

    st.divider()

    # 🎯 Top Issues
    st.subheader("🎯 Top Issues")
    for issue in get_top_issues(errors, slow):
        st.warning(issue)

    st.divider()

    # 📊 Charts
    st.subheader("📊 Status Code Distribution")
    status_counts = df["status"].value_counts()

    fig1 = plt.figure()
    status_counts.plot(kind='bar')
    st.pyplot(fig1)

    st.subheader("📊 Response Time Distribution")
    fig2 = plt.figure()
    df["time"].plot(kind='hist', bins=30)
    st.pyplot(fig2)

    st.divider()

    # 🌐 Domain Analysis
    st.subheader("🌐 Requests by Domain")
    domain_counts = df["domain"].value_counts().head(10)
    st.bar_chart(domain_counts)

    st.divider()

    # 📄 Tables
    st.subheader("🚨 Error Details")
    st.dataframe(errors.head(10))

    st.subheader("⏱️ Slow Requests")
    st.dataframe(slow.head(10))

    # 🧠 AI Insights
    if st.button("🧠 Generate AI Insights"):
        with st.spinner("Analyzing with AI..."):
            ai_output = get_ai_analysis(errors, slow)
            st.subheader("🧠 AI Insights")
            st.write(ai_output)

else:
    st.info("👆 Upload a HAR file to begin analysis")

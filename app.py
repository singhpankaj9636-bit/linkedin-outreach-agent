import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import csv
import io
from datetime import datetime

st.set_page_config(page_title="LinkedIn Outreach Agent", page_icon="🤝")

st.title("🤝 LinkedIn Outreach Agent")
st.markdown("**AI-powered B2B messages for SaaS founders**")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# Google Sheets setup
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["SHEET_ID"])
    try:
        worksheet = sh.worksheet("CRM")
    except:
        worksheet = sh.add_worksheet(title="CRM", rows="1000", cols="20")
        worksheet.append_row(["Date", "Name", "Title", "Company", "Stage", "Pain Point", "Connection Request", "Follow-up", "Cold Email", "CTA", "Personalization", "Reply Probability", "Spam Risk"])
    return worksheet

if "crm_data" not in st.session_state:
    st.session_state.crm_data = []
if "last_output" not in st.session_state:
    st.session_state.last_output = None

st.subheader("Target Lead Info")
prospect_name = st.text_input("Prospect's Name", placeholder="e.g. Rahul Sharma")
job_title = st.text_input("Their Job Title", placeholder="e.g. Founder & CEO")
company = st.text_input("Their Company", placeholder="e.g. Notion, Slack")
stage = st.selectbox("Company Stage", ["Early-stage Startup", "Series A SaaS", "Growth-stage SaaS", "Bootstrapped SaaS"])
pain_point = st.text_input("Their Pain Point", placeholder="e.g. outbound slowing down")
recent_activity = st.text_input("Their Recent Post / Activity (optional)", placeholder="e.g. posted about hiring SDRs")

st.subheader("Your Offer")
offer = st.text_input("What You're Offering", placeholder="e.g. AI agent that automates LinkedIn outreach")
benefit = st.text_input("Key Benefit", placeholder="e.g. saves 5 hours/week, 3x more replies")

st.subheader("Message Tone")
tone = st.radio("Select Tone", ["Professional", "Casual", "Friendly", "Direct", "Founder-style"], horizontal=True, label_visibility="collapsed")

st.subheader("Output Type")
output_type = st.multiselect(
    "Select what to generate:",
    ["Connection Request", "Follow-up Message", "Cold Email", "CTA Variation"],
    default=["Connection Request", "Follow-up Message"]
)

if st.button("⚡ Generate Messages", use_container_width=True):
    if not prospect_name or not company or not offer:
        st.error("Please fill Name, Company and Offer.")
    elif not output_type:
        st.error("Please select at least one output type.")
    else:
        with st.spinner("Generating..."):
            activity_context = f"Recent activity: {recent_activity}" if recent_activity else "No recent activity provided."
            outputs_needed = ", ".join(output_type)

            prompt = f"""You are an elite B2B outreach copywriter used by top SDRs and founders.

STRICT RULES:
- NEVER use generic hooks like "love what you're building" or "hope you're doing well"
- Hook must reference: specific pain point, recent activity, hiring signal, or scaling challenge
- Connection request: 2-3 lines MAX, ends with low-friction question, MAXIMUM 50 words
- Follow-up: 3-4 lines, lead with value NOT a pitch, soft CTA only, MAXIMUM 80 words
- Cold email: subject line first, blank line, then 4-5 SHORT lines with whitespace
- CTA variations: 4 options, ultra short, low pressure, conversational
- Tone: {tone}

FOUNDER STYLE RULES:
- Write like a founder, not a marketer
- Short sentences only
- NEVER use: "research suggests", "AI-powered solutions", "optimize outreach", "leverage automation"
- Sound human, not like a sales tool

PROSPECT INFO:
Name: {prospect_name}
Title: {job_title}
Company: {company}
Stage: {stage}
Pain point: {pain_point}
{activity_context}

YOUR OFFER: {offer}
Benefit: {benefit}

Generate ONLY these: {outputs_needed}

Use EXACTLY these headers:
CONNECTION REQUEST:
FOLLOW-UP MESSAGE:
COLD EMAIL:
CTA VARIATION:"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700
            )

            result = response.choices[0].message.content

            def safe_parse(text, header, next_headers):
                if header not in text:
                    return ""
                part = text.split(header)[1]
                for h in next_headers:
                    if h in part:
                        part = part.split(h)[0]
                return part.strip()

            conn = safe_parse(result, "CONNECTION REQUEST:", ["FOLLOW-UP MESSAGE:", "COLD EMAIL:", "CTA VARIATION:"])
            follow = safe_parse(result, "FOLLOW-UP MESSAGE:", ["COLD EMAIL:", "CTA VARIATION:"])
            email = safe_parse(result, "COLD EMAIL:", ["CTA VARIATION:"])
            cta = safe_parse(result, "CTA VARIATION:", [])

            if "Connection Request" in output_type and conn:
                st.subheader("📨 Connection Request")
                st.code(conn, language=None)

            if "Follow-up Message" in output_type and follow:
                st.subheader("💬 Follow-up Message")
                st.code(follow, language=None)

            if "Cold Email" in output_type and email:
                st.subheader("📧 Cold Email")
                st.code(email, language=None)

            if "CTA Variation" in output_type and cta:
                st.subheader("🎯 CTA Variations")
                st.code(cta, language=None)

            # Scoring
            st.markdown("---")
            st.subheader("📊 Message Score")

            score_prompt = f"""Analyze this outreach message strictly.

MESSAGE:
{result}

Prospect: {prospect_name}, {job_title} at {company}

OUTPUT FORMAT exactly:
PERSONALIZATION: X/10
REPLY PROBABILITY: X/10
SPAM RISK: X/10
TIP: one line improvement"""

            score_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": score_prompt}],
                max_tokens=150
            )

            score_text = score_response.choices[0].message.content
            lines = score_text.strip().split("\n")
            col1, col2, col3 = st.columns(3)

            p_score = r_score = s_score = 5
            tip = ""

            for line in lines:
                if "PERSONALIZATION:" in line:
                    try:
                        val = line.split(":")[1].strip().replace("/10","").strip()
                        p_score = float(val)
                        with col1:
                            st.metric("🎯 Personalization", f"{val}/10")
                            st.progress(p_score/10)
                    except: pass
                elif "REPLY PROBABILITY:" in line:
                    try:
                        val = line.split(":")[1].strip().replace("/10","").strip()
                        r_score = float(val)
                        with col2:
                            st.metric("📬 Reply Prob", f"{val}/10")
                            st.progress(r_score/10)
                    except: pass
                elif "SPAM RISK:" in line:
                    try:
                        val = line.split(":")[1].strip().replace("/10","").strip()
                        s_score = float(val)
                        with col3:
                            st.metric("🚨 Spam Risk", f"{val}/10")
                            st.progress(s_score/10)
                    except: pass
                elif "TIP:" in line:
                    tip = line.split("TIP:")[1].strip()
                    st.info(f"💡 {tip}")

            st.session_state.last_output = {
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Name": prospect_name,
                "Title": job_title,
                "Company": company,
                "Stage": stage,
                "Pain Point": pain_point,
                "Connection Request": conn,
                "Follow-up": follow,
                "Cold Email": email,
                "CTA": cta,
                "Personalization": f"{p_score}/10",
                "Reply Probability": f"{r_score}/10",
                "Spam Risk": f"{s_score}/10"
            }

# Save to Google Sheets
if st.session_state.last_output:
    if st.button("💾 Save to CRM (Google Sheets)", use_container_width=True):
        try:
            ws = get_sheet()
            row = list(st.session_state.last_output.values())
            ws.append_row(row)
            st.session_state.crm_data.append(st.session_state.last_output)
            st.success("✅ Saved to Google Sheets!")
        except Exception as e:
            st.error(f"Error: {e}")

# CRM Section
st.markdown("---")
st.subheader("📋 CRM — Saved Leads")

if st.session_state.crm_data:
    st.write(f"**{len(st.session_state.crm_data)} leads saved this session**")

    for lead in st.session_state.crm_data:
        with st.expander(f"👤 {lead['Name']} — {lead['Company']}"):
            st.write(f"**Title:** {lead['Title']}")
            st.write(f"**Stage:** {lead['Stage']}")
            if lead['Connection Request']:
                st.code(lead['Connection Request'], language=None)
            if lead['Follow-up']:
                st.code(lead['Follow-up'], language=None)
            st.write(f"**Scores:** P:{lead['Personalization']} | R:{lead['Reply Probability']} | S:{lead['Spam Risk']}")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=st.session_state.crm_data[0].keys())
    writer.writeheader()
    writer.writerows(st.session_state.crm_data)

    st.download_button(
        label="⬇️ Export CSV",
        data=output.getvalue(),
        file_name="linkedin_crm.csv",
        mime="text/csv",
        use_container_width=True
    )
else:
    st.info("No leads saved yet. Generate messages and click 'Save to CRM'.")

st.markdown("---")
st.caption("Built by Pankaj Singh · AI Agent Developer")

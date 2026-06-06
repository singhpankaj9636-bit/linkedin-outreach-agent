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

PIPELINE_STAGES = ["🟡 Sent", "🔵 Replied", "🟢 Meeting", "✅ Closed", "❌ Not Interested"]
SHEET_ID = "13-RUnaYI1r1TzVZ8NIFCrHH6eq7lDnNsPLkesM3B2jo"

# ── GOOGLE SHEETS CONNECTION ─────────────────────────────────────────────────
@st.cache_resource
def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.sheet1

    # Add headers if sheet is empty
    if not worksheet.get_all_values():
        headers = ["Date", "Name", "Title", "Company", "Stage", "Pain Point",
                   "Connection Request", "Follow-up", "Cold Email", "CTA",
                   "Personalization", "Reply Probability", "Spam Risk", "Pipeline Status"]
        worksheet.append_row(headers)
    return worksheet

def load_crm_from_sheet():
    try:
        ws = get_sheet()
        records = ws.get_all_records()
        return records
    except Exception as e:
        st.exception(e)
        return []

def save_lead_to_sheet(lead):
    try:
        ws = get_sheet()
        row = [
            lead.get("Date", ""),
            lead.get("Name", ""),
            lead.get("Title", ""),
            lead.get("Company", ""),
            lead.get("Stage", ""),
            lead.get("Pain Point", ""),
            lead.get("Connection Request", ""),
            lead.get("Follow-up", ""),
            lead.get("Cold Email", ""),
            lead.get("CTA", ""),
            lead.get("Personalization", ""),
            lead.get("Reply Probability", ""),
            lead.get("Spam Risk", ""),
            lead.get("Pipeline Status", "🟡 Sent")
        ]
        ws.append_row(row)
        return True
    except Exception as e:
        st.exception(e)
        return False

def update_status_in_sheet(row_index, new_status):
    try:
        ws = get_sheet()
        # +2 because row 1 is header, and gspread is 1-indexed
        ws.update_cell(row_index + 2, 14, new_status)
        return True
    except Exception as e:
        st.error(f"Update error: {e}")
        return False

def delete_lead_from_sheet(row_index):
    try:
        ws = get_sheet()
        ws.delete_rows(row_index + 2)
        return True
    except Exception as e:
        st.error(f"Delete error: {e}")
        return False

# ── SESSION STATE ────────────────────────────────────────────────────────────
if "last_output" not in st.session_state:
    st.session_state.last_output = None

# ── INPUT FORM ───────────────────────────────────────────────────────────────
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
tone = st.radio("", ["Professional", "Casual", "Friendly", "Direct", "Founder-style"], horizontal=True)

st.subheader("Output Type")
output_type = st.multiselect(
    "Select what to generate:",
    ["Connection Request", "Follow-up Message", "Cold Email", "CTA Variation"],
    default=["Connection Request", "Follow-up Message"]
)

# ── GENERATE ─────────────────────────────────────────────────────────────────
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

            # ── SCORING ──────────────────────────────────────────────────────
            st.markdown("---")
            st.subheader("📊 Message Score")

            score_prompt = f"""Analyze this outreach message strictly.
MESSAGE: {result}
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
                        val = line.split(":")[1].strip().replace("/10", "").strip()
                        p_score = float(val)
                        with col1:
                            st.metric("🎯 Personalization", f"{val}/10")
                            st.progress(p_score / 10)
                    except: pass
                elif "REPLY PROBABILITY:" in line:
                    try:
                        val = line.split(":")[1].strip().replace("/10", "").strip()
                        r_score = float(val)
                        with col2:
                            st.metric("📬 Reply Prob", f"{val}/10")
                            st.progress(r_score / 10)
                    except: pass
                elif "SPAM RISK:" in line:
                    try:
                        val = line.split(":")[1].strip().replace("/10", "").strip()
                        s_score = float(val)
                        with col3:
                            st.metric("🚨 Spam Risk", f"{val}/10")
                            st.progress(s_score / 10)
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
                "Spam Risk": f"{s_score}/10",
                "Pipeline Status": "🟡 Sent"
            }

# ── SAVE TO CRM ──────────────────────────────────────────────────────────────
if st.session_state.last_output:
    if st.button("💾 Save to CRM (Google Sheets)", use_container_width=True):
        success = save_lead_to_sheet(st.session_state.last_output)
        if success:
            st.success("✅ Saved to Google Sheets!")
            st.cache_resource.clear()

# ── CRM SECTION ──────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("📋 CRM — Pipeline Tracker")

crm_data = load_crm_from_sheet()

if crm_data:
    # ── PIPELINE SUMMARY ─────────────────────────────────────────────────────
    st.markdown("### 📊 Pipeline Summary")
    stage_counts = {s: 0 for s in PIPELINE_STAGES}
    for lead in crm_data:
        status = lead.get("Pipeline Status", "🟡 Sent")
        if status in stage_counts:
            stage_counts[status] += 1

    cols = st.columns(len(PIPELINE_STAGES))
    for i, (s, count) in enumerate(stage_counts.items()):
        with cols[i]:
            st.metric(s, count)

    st.markdown("---")

    # ── FILTER ───────────────────────────────────────────────────────────────
    filter_status = st.selectbox("🔍 Filter by Status", ["All"] + PIPELINE_STAGES)
    filtered = crm_data if filter_status == "All" else [
        l for l in crm_data if l.get("Pipeline Status") == filter_status
    ]
    st.write(f"**{len(filtered)} leads**")

    # ── LEAD CARDS ───────────────────────────────────────────────────────────
    for i, lead in enumerate(crm_data):
        if filter_status != "All" and lead.get("Pipeline Status") != filter_status:
            continue

        with st.expander(f"👤 {lead.get('Name','')} — {lead.get('Company','')} | {lead.get('Pipeline Status','🟡 Sent')}"):
            st.write(f"**Title:** {lead.get('Title','')}")
            st.write(f"**Stage:** {lead.get('Stage','')}")
            st.write(f"**Pain Point:** {lead.get('Pain Point','')}")
            st.write(f"**Date:** {lead.get('Date','')}")

            if lead.get('Connection Request'):
                st.markdown("**📨 Connection Request:**")
                st.code(lead['Connection Request'], language=None)
            if lead.get('Follow-up'):
                st.markdown("**💬 Follow-up:**")
                st.code(lead['Follow-up'], language=None)

            st.write(f"**Scores:** P:{lead.get('Personalization','')} | R:{lead.get('Reply Probability','')} | S:{lead.get('Spam Risk','')}")

            # Status update
            current_status = lead.get("Pipeline Status", "🟡 Sent")
            new_status = st.selectbox(
                "🔄 Update Status",
                PIPELINE_STAGES,
                index=PIPELINE_STAGES.index(current_status) if current_status in PIPELINE_STAGES else 0,
                key=f"status_{i}"
            )
            if st.button("✅ Update Status", key=f"update_{i}"):
                if update_status_in_sheet(i, new_status):
                    st.success(f"Updated to {new_status}!")
                    st.cache_resource.clear()
                    st.rerun()

            if st.button("🗑️ Delete Lead", key=f"delete_{i}"):
                if delete_lead_from_sheet(i):
                    st.success("Deleted!")
                    st.cache_resource.clear()
                    st.rerun()

    # ── CSV EXPORT ───────────────────────────────────────────────────────────
    st.markdown("---")
    if crm_data:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=crm_data[0].keys())
        writer.writeheader()
        writer.writerows(crm_data)
        st.download_button(
            label="⬇️ Export CRM as CSV",
            data=output.getvalue(),
            file_name="linkedin_outreach_crm.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("No leads saved yet. Generate messages and click 'Save to CRM'.")

st.markdown("---")
st.caption("Built by Pankaj Singh · AI Agent Developer")

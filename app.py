import streamlit as st
from groq import Groq
import gspread
from google.oauth2.service_account import Credentials
import csv
import io
from datetime import datetime

st.set_page_config(page_title="AI Outreach Copilot", page_icon="🚀", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background: #0A0F1E; color: #E2E8F0; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem; max-width: 1200px; }
.hero-badge { display: inline-flex; align-items: center; gap: 6px; background: rgba(124,58,237,0.15); border: 1px solid rgba(124,58,237,0.4); color: #A78BFA; padding: 5px 14px; border-radius: 50px; font-size: 12px; font-weight: 600; margin-bottom: 16px; }
.hero-title { font-size: 2.4rem; font-weight: 800; line-height: 1.2; color: #F8FAFC; margin: 0 0 10px 0; }
.hero-title span { background: linear-gradient(135deg,#7C3AED,#2563EB); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-subtitle { font-size: 1rem; color: #94A3B8; margin: 0 0 8px 0; }
.hero-tags { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.hero-tag { background: rgba(37,99,235,0.1); border: 1px solid rgba(37,99,235,0.25); color: #60A5FA; padding: 4px 12px; border-radius: 20px; font-size: 11px; font-weight: 500; }
.analytics-bar { display: flex; gap: 16px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 12px; padding: 14px 20px; margin: 20px 0; flex-wrap: wrap; }
.analytics-item { display: flex; flex-direction: column; gap: 2px; }
.analytics-value { font-size: 1.4rem; font-weight: 700; color: #F8FAFC; }
.analytics-label { font-size: 11px; color: #64748B; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.analytics-divider { width: 1px; background: rgba(255,255,255,0.07); margin: 0 4px; }
.section-header { font-size: 0.75rem; font-weight: 600; color: #7C3AED; text-transform: uppercase; letter-spacing: 1px; margin: 24px 0 12px 0; }
.score-card { background: linear-gradient(135deg,rgba(124,58,237,0.1),rgba(37,99,235,0.1)); border: 1px solid rgba(124,58,237,0.25); border-radius: 16px; padding: 24px; margin: 20px 0; }
.score-title { font-size: 0.85rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; }
.score-overall { font-size: 2rem; font-weight: 800; color: #A78BFA; }
.progress-bar-bg { width: 100%; height: 6px; background: rgba(255,255,255,0.07); border-radius: 10px; margin-top: 4px; overflow: hidden; }
.progress-bar-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg,#7C3AED,#2563EB); }
.progress-bar-warn { height: 100%; border-radius: 10px; background: linear-gradient(90deg,#F59E0B,#EF4444); }
.output-label { font-size: 11px; font-weight: 600; color: #7C3AED; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 10px; }
.crm-metric { background: linear-gradient(135deg,rgba(37,99,235,0.12),rgba(124,58,237,0.12)); border: 1px solid rgba(37,99,235,0.25); border-radius: 12px; padding: 16px 20px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; }
.crm-metric-value { font-size: 1.8rem; font-weight: 800; color: #60A5FA; }
.crm-metric-label { font-size: 0.8rem; color: #64748B; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.tip-box { background: rgba(37,99,235,0.08); border: 1px solid rgba(37,99,235,0.2); border-left: 3px solid #2563EB; border-radius: 8px; padding: 12px 16px; font-size: 0.85rem; color: #93C5FD; margin-top: 12px; }
.custom-divider { height: 1px; background: rgba(255,255,255,0.06); margin: 28px 0; }
.stButton > button { background: linear-gradient(135deg,#7C3AED,#2563EB) !important; color: white !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

if "crm_data" not in st.session_state:
    st.session_state.crm_data = []
if "last_output" not in st.session_state:
    st.session_state.last_output = None
if "messages_generated" not in st.session_state:
    st.session_state.messages_generated = 0
if "total_score" not in st.session_state:
    st.session_state.total_score = []

client = Groq(api_key=st.secrets["GROQ_API_KEY"])


def get_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(st.secrets["SHEET_ID"])
    try:
        worksheet = sh.worksheet("CRM")
    except Exception:
        worksheet = sh.add_worksheet(title="CRM", rows="1000", cols="20")
        worksheet.append_row(["Date","Name","Title","Company","Stage","Pain Point","Connection Request","Follow-up","Cold Email","CTA","Personalization","Reply Probability","Spam Risk"])
    return worksheet


st.markdown('<div class="hero-badge">🚀 AI-Powered Outreach Automation</div>', unsafe_allow_html=True)
st.markdown('<h1 class="hero-title">Generate Personalized B2B Outreach<br><span>That Gets More Replies</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="hero-subtitle">For SaaS Founders, Agencies & B2B Teams</p>', unsafe_allow_html=True)
st.markdown('<div class="hero-tags"><span class="hero-tag">✦ LinkedIn Messages</span><span class="hero-tag">✦ Cold Emails</span><span class="hero-tag">✦ Follow-ups</span><span class="hero-tag">✦ CRM Built-in</span></div>', unsafe_allow_html=True)

avg_score = round(sum(st.session_state.total_score) / len(st.session_state.total_score)) if st.session_state.total_score else 0
st.markdown(f"""
<div class="analytics-bar">
    <div class="analytics-item"><span class="analytics-value">{st.session_state.messages_generated}</span><span class="analytics-label">Messages Generated</span></div>
    <div class="analytics-divider"></div>
    <div class="analytics-item"><span class="analytics-value">{avg_score}%</span><span class="analytics-label">Avg Quality Score</span></div>
    <div class="analytics-divider"></div>
    <div class="analytics-item"><span class="analytics-value">{len(st.session_state.crm_data)}</span><span class="analytics-label">Leads Saved</span></div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">Lead Information</div>', unsafe_allow_html=True)

col_left, col_right = st.columns(2)
with col_left:
    prospect_name = st.text_input("Prospect Name", placeholder="e.g. Rahul Sharma")
    job_title = st.text_input("Job Title", placeholder="e.g. Founder & CEO")
    company = st.text_input("Company", placeholder="e.g. Notion, Slack")
with col_right:
    stage = st.selectbox("Company Stage", ["Early-stage Startup","Series A SaaS","Growth-stage SaaS","Bootstrapped SaaS"])
    tone = st.selectbox("Message Tone", ["Professional","Casual","Friendly","Direct","Founder-style"])
    output_type = st.multiselect("Output Type", ["Connection Request","Follow-up Message","Cold Email","CTA Variation"], default=["Connection Request","Follow-up Message"])

st.markdown('<div class="section-header">Context & Offer</div>', unsafe_allow_html=True)
col_a, col_b = st.columns(2)
with col_a:
    pain_point = st.text_input("Their Pain Point", placeholder="e.g. outbound slowing down")
    recent_activity = st.text_input("Recent Activity (optional)", placeholder="e.g. posted about hiring SDRs")
with col_b:
    offer = st.text_input("What You're Offering", placeholder="e.g. AI agent that automates outreach")
    benefit = st.text_input("Key Benefit", placeholder="e.g. saves 5 hours/week, 3x more replies")

st.markdown("<br>", unsafe_allow_html=True)

if st.button("⚡ Generate Messages", use_container_width=True):
    if not prospect_name or not company or not offer:
        st.error("Please fill Name, Company and Offer.")
    elif not output_type:
        st.error("Please select at least one output type.")
    else:
        with st.spinner("Crafting your outreach..."):
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
- Write like a founder, not a marketer. Short sentences only.

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

            conn = safe_parse(result, "CONNECTION REQUEST:", ["FOLLOW-UP MESSAGE:","COLD EMAIL:","CTA VARIATION:"])
            follow = safe_parse(result, "FOLLOW-UP MESSAGE:", ["COLD EMAIL:","CTA VARIATION:"])
            email = safe_parse(result, "COLD EMAIL:", ["CTA VARIATION:"])
            cta = safe_parse(result, "CTA VARIATION:", [])

            st.markdown('<div class="section-header">Generated Messages</div>', unsafe_allow_html=True)

            if "Connection Request" in output_type and conn:
                st.markdown('<div class="output-label">📨 Connection Request</div>', unsafe_allow_html=True)
                st.code(conn, language=None)

            if "Follow-up Message" in output_type and follow:
                st.markdown('<div class="output-label">💬 Follow-up Message</div>', unsafe_allow_html=True)
                st.code(follow, language=None)

            if "Cold Email" in output_type and email:
                st.markdown('<div class="output-label">📧 Cold Email</div>', unsafe_allow_html=True)
                st.code(email, language=None)

            if "CTA Variation" in output_type and cta:
                st.markdown('<div class="output-label">🎯 CTA Variations</div>', unsafe_allow_html=True)
                st.code(cta, language=None)

            score_prompt = f"""Analyze this outreach message strictly.
MESSAGE: {result}
Prospect: {prospect_name}, {job_title} at {company}
OUTPUT FORMAT exactly:
PERSONALIZATION: X/10
REPLY PROBABILITY: X/10
SPAM RISK: X/10
TIP: one line improvement"""

            score_response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": score_prompt}],
                max_tokens=150
            )
            score_text = score_response.choices[0].message.content
            lines = score_text.strip().split("\n")
            p_score = r_score = s_score = 5
            tip = ""
            for line in lines:
                if "PERSONALIZATION:" in line:
                    try:
                        p_score = float(line.split(":")[1].strip().replace("/10","").strip())
                    except Exception:
                        pass
                elif "REPLY PROBABILITY:" in line:
                    try:
                        r_score = float(line.split(":")[1].strip().replace("/10","").strip())
                    except Exception:
                        pass
                elif "SPAM RISK:" in line:
                    try:
                        s_score = float(line.split(":")[1].strip().replace("/10","").strip())
                    except Exception:
                        pass
                elif "TIP:" in line:
                    tip = line.split("TIP:")[1].strip()

            overall = round(((p_score + r_score + (10 - s_score)) / 30) * 100)
            st.session_state.total_score.append(overall)
            p_check = "✓" if p_score >= 7 else "⚠"
            r_check = "✓" if r_score >= 7 else "⚠"
            s_check = "✓" if s_score <= 3 else "⚠"
            warn_class = "progress-bar-warn" if s_score > 5 else "progress-bar-fill"
            tip_html = f'<div class="tip-box">💡 {tip}</div>' if tip else ""

            st.markdown(f"""
<div class="score-card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
        <div><div class="score-title">Message Quality Score</div><div style="color:#64748B;font-size:0.8rem;margin-top:2px;">Personalization · Reply Rate · Spam Risk</div></div>
        <div class="score-overall">{overall}/100</div>
    </div>
    <div style="display:flex;justify-content:space-between;"><span style="color:#CBD5E1;font-size:0.85rem;">{p_check} Personalization</span><span style="color:#F8FAFC;font-weight:700;">{int(p_score)}/10</span></div>
    <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:{int(p_score*10)}%"></div></div>
    <div style="display:flex;justify-content:space-between;margin-top:14px;"><span style="color:#CBD5E1;font-size:0.85rem;">{r_check} Reply Probability</span><span style="color:#F8FAFC;font-weight:700;">{int(r_score)}/10</span></div>
    <div class="progress-bar-bg"><div class="progress-bar-fill" style="width:{int(r_score*10)}%"></div></div>
    <div style="display:flex;justify-content:space-between;margin-top:14px;"><span style="color:#CBD5E1;font-size:0.85rem;">{s_check} Spam Risk</span><span style="color:#F8FAFC;font-weight:700;">{int(s_score)}/10</span></div>
    <div class="progress-bar-bg"><div class="{warn_class}" style="width:{int(s_score*10)}%"></div></div>
    {tip_html}
</div>
""", unsafe_allow_html=True)

            st.session_state.messages_generated += 1
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
                "Personalization": f"{int(p_score)}/10",
                "Reply Probability": f"{int(r_score)}/10",
                "Spam Risk": f"{int(s_score)}/10"
            }

if st.session_state.last_output:
    if st.button("💾 Save to CRM", use_container_width=True):
        try:
            ws = get_sheet()
            row = list(st.session_state.last_output.values())
            ws.append_row(row)
            st.session_state.crm_data.append(st.session_state.last_output)
            st.success("✅ Saved to Google Sheets!")
        except Exception as e:
            st.error(f"Error: {e}")

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="section-header">CRM — Saved Leads</div>', unsafe_allow_html=True)

if st.session_state.crm_data:
    recent_leads_html = "".join([f'<div style="font-size:0.8rem;color:#60A5FA;margin-top:3px;">• {lead["Name"]} — {lead["Company"]}</div>' for lead in st.session_state.crm_data[-3:]])
    st.markdown(f"""
<div class="crm-metric">
    <div><div class="crm-metric-value">{len(st.session_state.crm_data)}</div><div class="crm-metric-label">Total Leads Saved</div></div>
    <div style="text-align:right"><div style="font-size:0.85rem;color:#94A3B8;font-weight:500;">Recent Leads</div>{recent_leads_html}</div>
</div>
""", unsafe_allow_html=True)

    for lead in st.session_state.crm_data:
        with st.expander(f"👤 {lead['Name']} — {lead['Company']}"):
            st.write(f"**Title:** {lead['Title']} | **Stage:** {lead['Stage']}")
            if lead["Connection Request"]:
                st.code(lead["Connection Request"], language=None)
            if lead["Follow-up"]:
                st.code(lead["Follow-up"], language=None)
            st.write(f"**Scores:** P:{lead['Personalization']} | R:{lead['Reply Probability']} | S:{lead['Spam Risk']}")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=st.session_state.crm_data[0].keys())
    writer.writeheader()
    writer.writerows(st.session_state.crm_data)
    st.download_button(label="⬇️ Export CSV", data=output.getvalue(), file_name="outreach_crm.csv", mime="text/csv", use_container_width=True)
else:
    st.info("No leads saved yet. Generate messages and click Save to CRM.")

st.markdown('<div class="custom-divider"></div>', unsafe_allow_html=True)
st.markdown('<div style="text-align:center;color:#334155;font-size:0.8rem;padding:8px 0 16px 0;">Built by <strong style="color:#7C3AED">Pankaj Singh</strong> · AI Agent Developer · AI Outreach Copilot v2.0</div>', unsafe_allow_html=True)

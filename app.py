import streamlit as st
from groq import Groq

st.set_page_config(page_title="LinkedIn Outreach Agent", page_icon="🤝")

st.title("🤝 LinkedIn Outreach Agent")
st.markdown("**AI-powered B2B messages for SaaS founders**")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.subheader("Target Lead Info")
prospect_name = st.text_input("Prospect's Name", placeholder="e.g. Rahul Sharma")
job_title = st.text_input("Their Job Title", placeholder="e.g. Founder & CEO")
company = st.text_input("Their Company", placeholder="e.g. Notion, Slack")
stage = st.selectbox("Company Stage", ["Early-stage Startup", "Series A SaaS", "Growth-stage SaaS", "Bootstrapped SaaS"])
pain_point = st.text_input("Their Pain Point", placeholder="e.g. outbound slowing down, scaling sales team")
recent_activity = st.text_input("Their Recent Post / Activity (optional)", placeholder="e.g. posted about hiring SDRs, shared a post on B2B sales challenges")

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
- Connection request: 2-3 lines MAX, one specific observation, ends with a low-friction question
- Follow-up: 3-4 lines, lead with value/insight NOT a pitch, soft CTA only
- Cold email: subject line on first line, then blank line, then 4-5 SHORT lines with whitespace between each, end with one low-friction CTA
- CTA variations: 4 options, ultra short, low pressure, conversational
- Tone: {tone}
- Sound human, not like a sales tool

PROSPECT INFO:
Name: {prospect_name}
Title: {job_title}
Company: {company}
Stage: {stage}
Pain point: {pain_point}
{activity_context}

YOUR OFFER:
{offer}
Benefit: {benefit}

Generate ONLY these: {outputs_needed}

Use EXACTLY these headers:
CONNECTION REQUEST:
FOLLOW-UP MESSAGE:
COLD EMAIL:
CTA VARIATION:

Example of good connection request:
"Hey [Name] — noticed [specific observation about their pain/activity]. Curious how you're handling [specific challenge] right now?"

Example of good follow-up:
"Built a workflow recently that cut manual outreach time significantly. Happy to share the setup if it's useful — no pitch, just the approach."

Example of good CTAs:
"Worth a look?"
"Can send a quick example."
"Open to seeing the workflow?"
"Too noisy right now — totally fine."
"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=700
            )

            result = response.choices[0].message.content

            if "Connection Request" in output_type and "CONNECTION REQUEST:" in result:
                parts = result.split("CONNECTION REQUEST:")[1]
                conn = parts.split("FOLLOW-UP MESSAGE:")[0].strip() if "FOLLOW-UP MESSAGE:" in parts else parts.split("\n\n")[0].strip()
                st.subheader("📨 Connection Request")
                st.info(conn)
                st.code(conn, language=None)

            if "Follow-up Message" in output_type and "FOLLOW-UP MESSAGE:" in result:
                parts = result.split("FOLLOW-UP MESSAGE:")[1]
                follow = parts.split("COLD EMAIL:")[0].strip() if "COLD EMAIL:" in parts else parts.split("CTA VARIATION:")[0].strip() if "CTA VARIATION:" in parts else parts.strip()
                st.subheader("💬 Follow-up Message")
                st.success(follow)
                st.code(follow, language=None)

            if "Cold Email" in output_type and "COLD EMAIL:" in result:
                parts = result.split("COLD EMAIL:")[1]
                email = parts.split("CTA VARIATION:")[0].strip() if "CTA VARIATION:" in parts else parts.strip()
                st.subheader("📧 Cold Email")
                st.warning(email)
                st.code(email, language=None)

            if "CTA Variation" in output_type and "CTA VARIATION:" in result:
                parts = result.split("CTA VARIATION:")[1]
                cta = parts.strip()
                st.subheader("🎯 CTA Variations")
                st.error(cta)
                st.code(cta, language=None)

st.markdown("---")
st.caption("Built by Pankaj Singh · AI Agent Developer")

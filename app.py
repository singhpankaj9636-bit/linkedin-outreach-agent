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
pain_point = st.text_input("Their Pain Point", placeholder="e.g. struggling with B2B lead gen")

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
            outputs_needed = ", ".join(output_type)
            prompt = f"""You are an expert B2B LinkedIn copywriter. Write SHORT, HUMAN, CONVERSATIONAL messages.

RULES:
- Sound like a real founder texting another founder
- NO corporate speak, NO long paragraphs
- Connection request: max 3 lines, casual, ends with soft question
- Follow-up: max 4 short lines, personal opener, one clear CTA
- Cold email: subject line + 5 lines max, punchy, no fluff
- CTA variation: 3 different CTAs they can use, short and direct
- Tone: {tone}

PROSPECT: {prospect_name}, {job_title} at {company} ({stage})
PAIN POINT: {pain_point}
OFFER: {offer}
BENEFIT: {benefit}

Generate ONLY these outputs: {outputs_needed}

Use these exact headers for each section:
CONNECTION REQUEST:
FOLLOW-UP MESSAGE:
COLD EMAIL:
CTA VARIATION:"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=600
            )

            result = response.choices[0].message.content

            if "Connection Request" in output_type:
                if "CONNECTION REQUEST:" in result:
                    parts = result.split("CONNECTION REQUEST:")[1]
                    conn = parts.split("\n\n")[0].strip()
                    st.subheader("📨 Connection Request")
                    st.info(conn)
                    st.code(conn, language=None)

            if "Follow-up Message" in output_type:
                if "FOLLOW-UP MESSAGE:" in result:
                    parts = result.split("FOLLOW-UP MESSAGE:")[1]
                    follow = parts.split("\n\n")[0].strip()
                    st.subheader("💬 Follow-up Message")
                    st.success(follow)
                    st.code(follow, language=None)

            if "Cold Email" in output_type:
                if "COLD EMAIL:" in result:
                    parts = result.split("COLD EMAIL:")[1]
                    email = parts.split("\n\n")[0].strip()
                    st.subheader("📧 Cold Email")
                    st.warning(email)
                    st.code(email, language=None)

            if "CTA Variation" in output_type:
                if "CTA VARIATION:" in result:
                    parts = result.split("CTA VARIATION:")[1]
                    cta = parts.strip()
                    st.subheader("🎯 CTA Variations")
                    st.error(cta)
                    st.code(cta, language=None)

st.markdown("---")
st.caption("Built by Pankaj Singh · AI Agent Developer")

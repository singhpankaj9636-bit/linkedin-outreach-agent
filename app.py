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
tone = st.selectbox("Message Tone", ["Professional", "Casual", "Bold", "Warm"])

if st.button("⚡ Generate Messages", use_container_width=True):
    if not prospect_name or not company or not offer:
        st.error("Please fill Name, Company and Offer.")
    else:
        with st.spinner("Generating..."):
            prompt = f"""You are a B2B LinkedIn outreach expert for SaaS.

Generate TWO messages:

PROSPECT: {prospect_name}, {job_title} at {company} ({stage})
PAIN POINT: {pain_point}
OFFER: {offer}
BENEFIT: {benefit}
TONE: {tone}

CONNECTION REQUEST:
[Max 280 chars, personalized, ends with soft hook]

FOLLOW-UP MESSAGE:
[3-4 short paragraphs, personalized opener, natural pitch, one clear CTA]"""

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800
            )

            result = response.choices[0].message.content
            parts = result.split("FOLLOW-UP MESSAGE:")

            st.subheader("📨 Connection Request")
            st.info(parts[0].replace("CONNECTION REQUEST:", "").strip())

            if len(parts) > 1:
                st.subheader("💬 Follow-up Message")
                st.success(parts[1].strip())

st.markdown("---")
st.caption("Built by Pankaj Singh · AI Agent Developer")

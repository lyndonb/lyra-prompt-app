import streamlit as st
import pandas as pd
from datetime import datetime
import json
from pathlib import Path

st.set_page_config(page_title="Lyra Prompt App", page_icon="✨", layout="wide")

APP_DIR = Path(__file__).parent

# Load templates if available
templates_file = APP_DIR / "templates.csv"
if templates_file.exists():
    templates_df = pd.read_csv(templates_file)
else:
    templates_df = pd.DataFrame(columns=["ID", "Category", "Rough Idea", "Tags", "Suggested Clarifying Questions"])

BRAND_PRIMARY = "#6C5CE7"
BRAND_ACCENT = "#00CEC9"

# --- Sidebar ---
with st.sidebar:
    st.markdown("## ✨ Lyra Prompt App")
    st.caption("Your personal AI prompt consultant — type messy, get magic.")

    target_ai = st.selectbox("Target AI", ["ChatGPT", "Claude", "Gemini", "Other"], index=0)
    mode = st.selectbox("Prompt Style", ["DETAIL", "BASIC"], index=0)

    st.divider()
    st.markdown("**Load a Starter Template (optional)**")

    if not templates_df.empty:
        categories = ["All"] + sorted(templates_df["Category"].unique().tolist())
        cat_choice = st.selectbox("Category", categories, index=0)
        subset = templates_df if cat_choice == "All" else templates_df[templates_df["Category"] == cat_choice]
        label_map = {f"[{r.Category}] {r['Rough Idea']}": int(r.ID) for _, r in subset.iterrows()}
        pick = st.selectbox("Pick a template", ["(none)"] + list(label_map.keys()), index=0)
        selected = None
        if pick != "(none)":
            selected = templates_df.loc[templates_df.ID == label_map[pick]].iloc[0]
    else:
        st.caption("⚠️ No templates found. You can add templates.csv later.")
        selected = None

    st.divider()
    export_history = st.checkbox("Auto-save session history (CSV)", value=True)

# --- Header ---
st.markdown(
    f"""
    <div style='padding:12px 16px;border-radius:16px;
        background:linear-gradient(135deg,{BRAND_PRIMARY},{BRAND_ACCENT});
        color:#111;font-weight:700;'>
      <span style='font-size:20px;'>✨ Lyra Prompt App</span>
      <span style='font-size:14px;margin-left:8px;font-weight:500;'>
      — Turn rough ideas into optimized prompts.</span>
    </div>
    """,
    unsafe_allow_html=True
)

left, right = st.columns(2)

# --- Left column: Input ---
with left:
    st.subheader("1) Your Rough Prompt")
    default_text = selected["Rough Idea"] if selected is not None else ""
    rough = st.text_area("Type anything (the messier the better):", value=default_text,
                         height=120, placeholder="e.g., Write me a sales email")

    st.subheader("2) Clarifying (auto in DETAIL)")
    if mode == "DETAIL":
        hints = selected["Suggested Clarifying Questions"] if selected is not None else \
            "Who is the audience? What outcome? Any constraints (length, tone, format)?"
        st.caption(f"Suggested prompts: {hints}")
        q1 = st.text_input("Answer 1")
        q2 = st.text_input("Answer 2")
        q3 = st.text_input("Answer 3")
        answers = {k: v for k, v in {"A1": q1, "A2": q2, "A3": q3}.items() if v.strip() != ""}
    else:
        answers = {}

    st.subheader("3) Output Specs (optional)")
    tokens = st.text_input("Max length / tokens (optional)", value="")
    extras = st.text_area("Special instructions (style guides, constraints)", value="", height=80)

# --- Right column: Output ---
with right:
    st.subheader("Your Optimized Prompt")
    st.caption("Copy this into your chosen AI (or paste into the chat you already have open).")

    def build_prompt(rough, target_ai, mode, answers_dict, tokens, extras):
        if not rough.strip():
            return ""
        lines = []
        lines.append(f"You are Lyra, optimizing a user request for {target_ai}.")
        lines.append("Follow the 4-D method: Deconstruct, Diagnose, Develop, Deliver.")
        lines.append("Return a final, ready-to-run prompt for the target AI.")
        lines.append("")
        lines.append("=== INPUT ===")
        lines.append(rough.strip())
        lines.append("")
        if mode == "DETAIL" and answers_dict:
            lines.append("=== USER ANSWERS ===")
            for k, v in answers_dict.items():
                lines.append(f"- {k}: {v}")
            lines.append("")
        lines.append("=== REQUIREMENTS ===")
        if tokens.strip():
            lines.append(f"- Max length/tokens: {tokens.strip()}")
        if extras.strip():
            lines.append(f"- Special constraints: {extras.strip()}")
        lines.append("- Output must be specific, unambiguous, and formatted for easy copy-paste.")
        lines.append("")
        lines.append("=== DELIVERABLE FORMAT ===")
        lines.append("**Your Optimized Prompt:**")
        lines.append("[Write the improved prompt here]")
        lines.append("")
        lines.append("**Key Improvements:**")
        lines.append("• Bullet point 1")
        lines.append("• Bullet point 2")
        lines.append("")
        lines.append("**Techniques Applied:** Chain-of-thought (internal), role assignment, context layering, output specs.")
        lines.append("")
        lines.append("**Pro Tip:** Suggest how to iterate if the first output isn't perfect.")
        return "\n".join(lines)

    optimized = build_prompt(rough, target_ai, mode, answers, tokens, extras)
    st.code(optimized or "← Start by typing a rough prompt on the left.", language="markdown")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("Download .txt", data=optimized, file_name="optimized_prompt.txt", disabled=not optimized)
    with c2:
        st.button("Copy to Clipboard", disabled=True,
                  help="Use Download or manual copy. (Clipboard component can be added later.)")
    with c3:
        st.download_button("Download .md", data=optimized, file_name="optimized_prompt.md", disabled=not optimized)

# --- History ---
st.divider()
st.subheader("Session History")
history_path = APP_DIR / "history.csv"
if export_history and optimized:
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "target_ai": target_ai,
        "mode": mode,
        "rough": rough,
        "answers_json": json.dumps(answers),
        "tokens": tokens,
        "extras": extras,
        "optimized_len": len(optimized)
    }
    if history_path.exists():
        dfh = pd.read_csv(history_path)
        dfh = pd.concat([dfh, pd.DataFrame([row])], ignore_index=True)
    else:
        dfh = pd.DataFrame([row])
    dfh.to_csv(history_path, index=False)

if history_path.exists():
    dfh = pd.read_csv(history_path)
    st.dataframe(dfh.tail(20), use_container_width=True)
else:
    st.caption("No sessions saved yet. Enable auto-save to log runs.")


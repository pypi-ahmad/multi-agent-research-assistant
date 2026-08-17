"""Streamlit UI for the multi-agent research assistant."""

from __future__ import annotations

from datetime import datetime

import streamlit as st

import config
import memory
from graph import initial_state, research_graph
from tools.pdf_loader import extract_pdf_text

st.set_page_config(page_title="Multi-Agent Research Assistant", layout="wide")

AGENT_LABELS = {
    "planner": "🧭 Planner — building research plan",
    "researcher": "🔎 Researcher — gathering sources",
    "critic": "🧪 Critic — scoring & evaluating sources",
    "reflector": "🔁 Reflector — deciding whether more research is needed",
    "writer": "✍️ Writer — synthesizing final report",
}

# Mirrors the Annotated[..., operator.add] reducers declared in state.py, so we
# can reconstruct the final accumulated state from a stream of per-node deltas
# without invoking the graph a second time.
_ACCUMULATING_LIST_KEYS = {"research_results", "errors"}
_ACCUMULATING_INT_KEYS = {"step_count"}


def _merge_update(acc: dict, update: dict) -> dict:
    for key, value in update.items():
        if key in _ACCUMULATING_LIST_KEYS:
            acc[key] = acc.get(key, []) + value
        elif key in _ACCUMULATING_INT_KEYS:
            acc[key] = acc.get(key, 0) + value
        else:
            acc[key] = value
    return acc


def _report_to_pdf_bytes(report_text: str) -> bytes:
    # ponytail: fpdf2 core fonts are latin-1 only, so GPT-styled punctuation
    # (em dashes, curly quotes) gets replaced with "?" in the PDF; the
    # Markdown download is unaffected. Upgrade path if this matters: embed a
    # unicode TTF font via pdf.add_font(...).
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    safe_text = report_text.encode("latin-1", "replace").decode("latin-1")
    for line in safe_text.split("\n"):
        pdf.multi_cell(0, 6, line)
    return bytes(pdf.output())


def run_research(
    query: str, depth: str, local_model: str, reasoning_provider: str, pdf_text: str, previous_context: str
) -> dict:
    state = initial_state(
        query, depth, local_model, reasoning_provider,
        uploaded_pdf_text=pdf_text, previous_context=previous_context,
    )
    if pdf_text:
        state["research_results"].append(
            {
                "subquestion": "user-uploaded document",
                "title": "Uploaded PDF",
                "url": "uploaded://document.pdf",
                "snippet": pdf_text[:1000],
                "summary": pdf_text[:1000],
                "source_type": "pdf",
                "published": None,
            }
        )

    acc = dict(state)
    with st.status("Running research...", expanded=True) as status:
        for event in research_graph.stream(state, stream_mode="updates"):
            for node_name, update in event.items():
                acc = _merge_update(acc, update)
                status.write(AGENT_LABELS.get(node_name, node_name))
        status.update(label="Research complete", state="complete")
    return acc


def _render_result(result: dict) -> None:
    plan_tab, sources_tab, critique_tab, report_tab = st.tabs(
        ["Plan", "Sources", "Critic Feedback", "Final Report"]
    )

    with plan_tab:
        st.write(result.get("plan_rationale", ""))
        for i, sq in enumerate(result.get("plan", []), start=1):
            st.markdown(f"{i}. {sq}")

    with sources_tab:
        sources = sorted(result.get("sources", []), key=lambda s: s.get("trust_score", 0), reverse=True)
        if not sources:
            st.info("No sources gathered.")
        for s in sources:
            included = s.get("trust_score", 0) >= config.MIN_TRUST_SCORE
            marker = "✅" if included else "⚠️ below threshold"
            with st.expander(f"{marker} {s.get('title', 'Untitled')} — trust {s.get('trust_score', 0)}/10"):
                st.write(s.get("summary", s.get("snippet", "")))
                st.caption(
                    f"Authority {s.get('authority', 0)} · Relevance {s.get('relevance', 0)} · "
                    f"Recency {s.get('recency', 0)} · {s.get('source_type', 'web')}"
                )
                if s.get("url", "").startswith("http"):
                    st.markdown(f"[{s['url']}]({s['url']})")

    with critique_tab:
        critique = result.get("critique", {})
        st.write(critique.get("notes", ""))
        if critique.get("gaps"):
            st.markdown("**Remaining gaps:**")
            for g in critique["gaps"]:
                st.markdown(f"- {g}")
        if critique.get("conflicting_info"):
            st.markdown("**Conflicting information found:**")
            for c in critique["conflicting_info"]:
                st.markdown(f"- {c}")
        if result.get("errors"):
            st.markdown("**Warnings during this run:**")
            for e in result["errors"]:
                st.caption(f"⚠️ {e}")

    with report_tab:
        report = result.get("final_report", "")
        st.markdown(report)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download as Markdown",
                data=report,
                file_name="research_report.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with col2:
            try:
                pdf_bytes = _report_to_pdf_bytes(report)
                st.download_button(
                    "⬇️ Download as PDF",
                    data=pdf_bytes,
                    file_name="research_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as exc:  # noqa: BLE001
                st.caption(f"PDF export unavailable: {exc}")


def main() -> None:
    st.session_state.setdefault("active_result", None)
    st.session_state.setdefault("active_session_id", None)

    st.sidebar.header("📚 Past Research")
    sessions = sorted(memory.load_all_sessions(), key=lambda s: s["timestamp"], reverse=True)
    if not sessions:
        st.sidebar.caption("No past research yet.")
    for session in sessions[:20]:
        ts = datetime.fromisoformat(session["timestamp"]).strftime("%Y-%m-%d %H:%M")
        with st.sidebar.expander(f"{session['query'][:40]} ({ts})"):
            st.caption(f"Depth: {session['depth']} · Model: {session['local_model']}")
            if st.button("Load", key=f"load_{session['id']}"):
                st.session_state.active_result = {
                    "plan": session["plan"],
                    "plan_rationale": "",
                    "sources": session["sources"],
                    "critique": {},
                    "final_report": session["report"],
                    "errors": [],
                    "query": session["query"],
                    "depth": session["depth"],
                    "local_model": session["local_model"],
                }
                st.session_state.active_session_id = session["id"]
                st.rerun()
            if st.button("Delete", key=f"delete_{session['id']}"):
                memory.delete_session(session["id"])
                st.rerun()

    st.title("🔬 Multi-Agent Research Assistant")
    st.caption("Planner → Researcher → Critic → Reflector → Writer, built on LangGraph.")

    query = st.text_area("Research query", placeholder="e.g. What are the tradeoffs of RAG vs fine-tuning?")

    col1, col2, col3 = st.columns(3)
    with col1:
        depth = st.radio("Depth of research", list(config.DEPTH_PRESETS.keys()), index=1, horizontal=True)
    with col2:
        local_model = st.selectbox("Local model (Ollama)", config.AVAILABLE_LOCAL_MODELS)
    with col3:
        reasoning_provider = st.selectbox(
            "Reasoning model (planner/critic/writer)",
            config.REASONING_PROVIDERS,
            index=config.REASONING_PROVIDERS.index(config.DEFAULT_REASONING_PROVIDER),
        )

    reasoning_key_set = (
        config.AGNES_API_KEY if reasoning_provider == "Agnes 2.5 Flash" else config.OPENAI_API_KEY
    )
    if not reasoning_key_set:
        env_name = "AGNES_API_KEY" if reasoning_provider == "Agnes 2.5 Flash" else "OPENAI_API_KEY"
        st.warning(f"{env_name} is not set. Planning, critique, and final synthesis need it — see .env.example.")

    uploaded_pdf = st.file_uploader("Optional: upload a reference PDF", type=["pdf"])
    pdf_text = ""
    if uploaded_pdf is not None:
        try:
            pdf_text = extract_pdf_text(uploaded_pdf.read())
            st.caption(f"Extracted {len(pdf_text)} characters from {uploaded_pdf.name}.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Could not read PDF: {exc}")

    if st.button("🚀 Start Research", type="primary", disabled=not query.strip()):
        try:
            result = run_research(
                query.strip(), depth, local_model, reasoning_provider, pdf_text, previous_context=""
            )
            session_id = memory.save_session(
                query.strip(), depth, local_model, result.get("plan", []), result.get("sources", []),
                result.get("final_report", ""),
            )
            result["query"], result["depth"], result["local_model"] = query.strip(), depth, local_model
            result["reasoning_provider"] = reasoning_provider
            st.session_state.active_result = result
            st.session_state.active_session_id = session_id
        except Exception as exc:  # noqa: BLE001
            st.error(f"Research run failed: {exc}")

    if st.session_state.active_result:
        st.divider()
        _render_result(st.session_state.active_result)

        st.divider()
        st.subheader("Follow-up question")
        followup = st.text_input("Ask a follow-up to dig deeper on the same topic")
        if st.button("Continue Research", disabled=not followup.strip()):
            prior = st.session_state.active_result
            previous_context = memory.summarize_for_followup({"report": prior.get("final_report", "")})
            try:
                result = run_research(
                    followup.strip(), prior.get("depth", "Standard"), prior.get("local_model", local_model),
                    prior.get("reasoning_provider", reasoning_provider),
                    pdf_text="", previous_context=previous_context,
                )
                session_id = memory.save_session(
                    followup.strip(), prior.get("depth", "Standard"), prior.get("local_model", local_model),
                    result.get("plan", []), result.get("sources", []), result.get("final_report", ""),
                    session_id=st.session_state.active_session_id,
                )
                result["query"], result["depth"], result["local_model"] = (
                    followup.strip(), prior.get("depth", "Standard"), prior.get("local_model", local_model),
                )
                st.session_state.active_result = result
                st.session_state.active_session_id = session_id
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Follow-up research failed: {exc}")


if __name__ == "__main__":
    main()

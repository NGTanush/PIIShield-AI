"""Page: Experiment History & Research Audit Trail.

Comprehensive historical log of all experiments with provenance tracking,
filtering, detailed metric inspection, and CSV export.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database.db_manager import get_all_experiments, clear_all_experiments
from dashboard.styles import metric_card, status_badge, data_panel


def render():
    """Render the Experiment History page."""
    st.markdown('<h1>📜 Experiment History & Research Audit Trail</h1>', unsafe_allow_html=True)
    st.markdown(
        "Complete provenance-tracked audit records for every evaluation run. "
        "Strictly records only masked text, failure distributions, and metrics — "
        "raw personal information is never persisted."
    )

    experiments = get_all_experiments(exclude_tests=True)

    if not experiments:
        st.info("No recorded experiments found. Run a prompt through **🤖 LLM Processing** and **🔐 Validation & Restoration**, then commit it on **📈 Research Evaluation**.")
        return

    df = pd.DataFrame(experiments)

    # ── Top Summary Cards ───────────────────────────────────────────────
    st.markdown('<div class="section-header"><h3>📊 Log Overview</h3></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)

    total_runs = len(df)
    real_llm_count = sum(1 for p in df.get("data_provenance", []) if p == "real_llm")
    bench_count = sum(1 for p in df.get("data_provenance", []) if p in ("benchmark", "simulated"))
    avg_f1 = df["f1_score"].mean() if "f1_score" in df.columns else 0.0

    with c1:
        st.markdown(metric_card("🧪", "Total Experiments", total_runs, "blue"), unsafe_allow_html=True)
    with c2:
        st.markdown(metric_card("🤖", "Real LLM Runs", real_llm_count, "green"), unsafe_allow_html=True)
    with c3:
        st.markdown(metric_card("📊", "Benchmark Runs", bench_count, "violet"), unsafe_allow_html=True)
    with c4:
        st.markdown(metric_card("🎯", "Average F1", f"{avg_f1*100:.1f}%", "cyan"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Interactive Filter Bar ──────────────────────────────────────────
    st.markdown("##### 🔍 Filter & Search Audit Trail")
    fcol1, fcol2, fcol3 = st.columns(3)

    with fcol1:
        prov_options = ["All"] + sorted(list(df["data_provenance"].dropna().unique())) if "data_provenance" in df.columns else ["All"]
        sel_prov = st.selectbox("Provenance Filter", prov_options)
    with fcol2:
        strat_options = ["All"] + sorted(list(df["placeholder_strategy"].dropna().unique())) if "placeholder_strategy" in df.columns else ["All"]
        sel_strat = st.selectbox("Strategy Filter", strat_options)
    with fcol3:
        scen_options = ["All"] + sorted(list(df["llm_scenario"].dropna().unique())) if "llm_scenario" in df.columns else ["All"]
        sel_scen = st.selectbox("Scenario Filter", scen_options)

    filtered_df = df.copy()
    if sel_prov != "All":
        filtered_df = filtered_df[filtered_df["data_provenance"] == sel_prov]
    if sel_strat != "All":
        filtered_df = filtered_df[filtered_df["placeholder_strategy"] == sel_strat]
    if sel_scen != "All":
        filtered_df = filtered_df[filtered_df["llm_scenario"] == sel_scen]

    st.caption(f"Showing **{len(filtered_df)}** of **{len(df)}** experiments.")

    # ── Table Display ───────────────────────────────────────────────────
    display_cols = [
        "id", "name", "created_at", "data_provenance", "placeholder_strategy",
        "llm_scenario", "num_entities_detected", "num_correct", "num_failed",
        "precision_score", "recall_score", "f1_score", "placeholder_preservation_rate"
    ]
    avail_cols = [c for c in display_cols if c in filtered_df.columns]
    disp_df = filtered_df[avail_cols].copy()
    disp_df.columns = [c.replace("_", " ").title() for c in avail_cols]
    st.dataframe(disp_df, use_container_width=True, hide_index=True)

    # ── Detailed Experiment Inspection Drill-Down ───────────────────────
    st.markdown("---")
    st.markdown("##### 🔎 Drill-Down Inspection")
    exp_ids = list(filtered_df["id"].values) if not filtered_df.empty else []
    if exp_ids:
        selected_exp_id = st.selectbox("Select Experiment ID to Inspect:", exp_ids)
        row = filtered_df[filtered_df["id"] == selected_exp_id].iloc[0]

        rcol1, rcol2, rcol3 = st.columns(3)
        with rcol1:
            st.markdown(f"**Experiment:** `{row.get('name')}`")
            st.markdown(f"**Provenance:** {status_badge(str(row.get('data_provenance')).upper(), 'success' if row.get('data_provenance')=='real_llm' else 'info')}", unsafe_allow_html=True)
        with rcol2:
            st.markdown(f"**Strategy:** `{row.get('placeholder_strategy')}`")
            st.markdown(f"**Scenario:** `{row.get('llm_scenario')}`")
        with rcol3:
            st.markdown(f"**Precision:** `{row.get('precision_score', 0)*100:.1f}%` | **Recall:** `{row.get('recall_score', 0)*100:.1f}%`")
            st.markdown(f"**F1 Score:** `{row.get('f1_score', 0)*100:.1f}%`")

        st.markdown("<br>", unsafe_allow_html=True)

        scol1, scol2 = st.columns(2)
        with scol1:
            st.markdown("###### 🔒 Masked Input Transmitted to LLM")
            st.markdown(data_panel(row.get("masked_text", "")), unsafe_allow_html=True)
            st.markdown("###### 📥 Raw LLM Response")
            st.markdown(data_panel(row.get("raw_llm_response", "")), unsafe_allow_html=True)
        with scol2:
            st.markdown("###### 🔓 Restored Downstream Output")
            st.markdown(data_panel(row.get("restored_response", "")), unsafe_allow_html=True)

            # Failure Breakdown mini-table
            st.markdown("###### 📋 Failure Breakdown")
            fail_data = {
                "Metric": ["Correct Restorations", "Dropped", "Inflected", "Mistranslated", "Hallucinated", "Cross-Wired"],
                "Count": [
                    row.get("num_correct", 0),
                    row.get("num_dropped", 0),
                    row.get("num_inflected", 0),
                    row.get("num_mistranslated", 0),
                    row.get("num_hallucinated", 0),
                    row.get("num_cross_wired", 0),
                ]
            }
            st.dataframe(pd.DataFrame(fail_data), use_container_width=True, hide_index=True)

    # ── Export & Clean Operations ───────────────────────────────────────
    st.markdown("---")
    ecol1, ecol2 = st.columns(2)
    with ecol1:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Export Full Experiment Audit Log (CSV)",
            data=csv_bytes,
            file_name=f"piishield_experiments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with ecol2:
        if st.button("🗑️ Clear Experiment History Database", use_container_width=True):
            clear_all_experiments()
            st.success("Experiment history database cleared.")
            st.rerun()


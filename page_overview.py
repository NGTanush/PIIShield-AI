"""
Page 1: Overview Dashboard.
Provides real-time mathematical aggregates, data provenance tracking,
and empirical failure distributions across experiment history.
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database.db_manager import get_dashboard_stats
from dashboard.styles import metric_card, status_badge


def render():
    """Render the Overview Dashboard page."""
    st.markdown('<h1>📊 Overview Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("Real-time metrics, data provenance, and round-trip restoration fidelity for PIIShield AI.")
    
    stats = get_dashboard_stats()
    
    # ── Top metric cards ──────────────────────────────────
    st.markdown('<div class="section-header"><h3>🔑 System Aggregates</h3></div>', unsafe_allow_html=True)
    
    cols = st.columns(4)
    with cols[0]:
        st.markdown(metric_card("🧪", "Total Experiments", stats["total_experiments"], "blue"),
                     unsafe_allow_html=True)
    with cols[1]:
        st.markdown(metric_card("🔍", "PII Entities Detected", stats["total_entities"], "violet"),
                     unsafe_allow_html=True)
    with cols[2]:
        st.markdown(metric_card("✅", "Successful Restorations", stats["total_correct"], "green"),
                     unsafe_allow_html=True)
    with cols[3]:
        st.markdown(metric_card("❌", "Failed Restorations", stats["total_failed"], "red"),
                     unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Mathematical Restoration Fidelity Cards (Micro-Average) ───────
    st.markdown('<div class="section-header"><h3>🎯 Round-Trip Restoration Fidelity (Mathematically Sound)</h3></div>', unsafe_allow_html=True)
    cols2 = st.columns(4)
    with cols2[0]:
        fidelity = f"{stats['micro_f1'] * 100:.1f}%" if stats['total_experiments'] > 0 else "N/A"
        st.markdown(metric_card("🎯", "Restoration F1", fidelity, "cyan"),
                     unsafe_allow_html=True)
    with cols2[1]:
        prec = f"{stats['micro_precision'] * 100:.1f}%" if stats['total_experiments'] > 0 else "N/A"
        st.markdown(metric_card("📏", "Restoration Precision", prec, "blue"),
                     unsafe_allow_html=True)
    with cols2[2]:
        rec = f"{stats['micro_recall'] * 100:.1f}%" if stats['total_experiments'] > 0 else "N/A"
        st.markdown(metric_card("📐", "Restoration Recall", rec, "violet"),
                     unsafe_allow_html=True)
    with cols2[3]:
        pres = f"{stats['avg_preservation'] * 100:.1f}%" if stats['total_experiments'] > 0 else "N/A"
        st.markdown(metric_card("🛡️", "Preservation Rate", pres, "green"),
                     unsafe_allow_html=True)

    # ── Data Provenance Pill Header ────────────────────────
    if stats["total_experiments"] > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        prov = stats.get("provenance_breakdown", {})
        prov_cols = st.columns(3)
        with prov_cols[0]:
            st.markdown(f"**Real LLM Runs:** `{prov.get('real_llm', 0)}`")
        with prov_cols[1]:
            st.markdown(f"**Simulated / Demo Runs:** `{prov.get('simulated', 0)}`")
        with prov_cols[2]:
            st.markdown(f"**Benchmark Dataset Runs:** `{prov.get('benchmark', 0)}`")
    
    # ── Charts ────────────────────────────────────────────
    recent = stats["recent_experiments"]
    
    if recent:
        st.markdown('<div class="section-header"><h3>📈 Empirical Performance & Failure Profiles</h3></div>',
                     unsafe_allow_html=True)
        
        df = pd.DataFrame(recent)
        col_a, col_b = st.columns(2)
        
        with col_a:
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df["name"], y=df["precision_score"],
                mode="lines+markers", name="Precision",
                line=dict(color="#3b82f6", width=2),
                marker=dict(size=8)
            ))
            fig.add_trace(go.Scatter(
                x=df["name"], y=df["recall_score"],
                mode="lines+markers", name="Recall",
                line=dict(color="#8b5cf6", width=2),
                marker=dict(size=8)
            ))
            fig.add_trace(go.Scatter(
                x=df["name"], y=df["f1_score"],
                mode="lines+markers", name="F1 Score",
                line=dict(color="#06b6d4", width=2),
                marker=dict(size=8)
            ))
            fig.update_layout(
                title="Restoration Metrics by Experiment Run",
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter", color="#94a3b8"),
                height=380,
                yaxis=dict(range=[0, 1.05], title="Score"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col_b:
            total_correct = sum(r.get("num_correct", 0) for r in recent)
            total_dropped = sum(r.get("num_dropped", 0) for r in recent)
            total_inflected = sum(r.get("num_inflected", 0) for r in recent)
            total_missed = sum(r.get("num_missed", 0) for r in recent)
            total_mistranslated = sum(r.get("num_mistranslated", 0) for r in recent)
            total_hallucinated = sum(r.get("num_hallucinated", 0) for r in recent)
            total_cross_wired = sum(r.get("num_cross_wired", 0) for r in recent)
            
            labels = ["Correct", "Dropped", "Inflected", "Missed", "Mistranslated", "Hallucinated", "Cross-wired"]
            values = [total_correct, total_dropped, total_inflected, total_missed,
                      total_mistranslated, total_hallucinated, total_cross_wired]
            colors = ["#10b981", "#ef4444", "#f59e0b", "#f97316", "#8b5cf6", "#ec4899", "#06b6d4"]
            
            filtered = [(l, v, c) for l, v, c in zip(labels, values, colors) if v > 0]
            if filtered:
                fl, fv, fc = zip(*filtered)
                fig2 = go.Figure(data=[go.Pie(
                    labels=list(fl), values=list(fv),
                    marker=dict(colors=list(fc)),
                    hole=0.4,
                    textinfo="label+percent",
                    textfont=dict(size=12),
                )])
                fig2.update_layout(
                    title="Failure Category Breakdown",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter", color="#94a3b8"),
                    height=380,
                    showlegend=False,
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No failure occurrences to display.")
        
        # Recent experiments table
        st.markdown('<div class="section-header"><h3>🕒 Recent Experiment Runs</h3></div>',
                     unsafe_allow_html=True)
        
        display_df = df[["id", "name", "created_at", "data_provenance", "placeholder_strategy",
                          "llm_scenario", "num_entities_detected", "num_correct",
                          "precision_score", "recall_score", "f1_score"]].copy()
        display_df.columns = ["ID", "Name", "Timestamp", "Provenance", "Strategy",
                               "Scenario", "Entities", "Correct", "Precision", "Recall", "F1"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    else:
        st.markdown("---")
        st.info("🚀 No experiments recorded yet. Use **📚 Research Dataset** or **🔍 PII Detection & Masking** to execute a benchmark run!")

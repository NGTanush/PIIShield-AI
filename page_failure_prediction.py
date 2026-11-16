"""Page: ML Failure Prediction for PIIShield AI."""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _load_predictor():
    try:
        from evaluation.failure_predictor import (
            predict_failure_probability, predict_batch,
            train_model, get_model_metadata
        )
        return predict_failure_probability, predict_batch, train_model, get_model_metadata
    except ImportError as e:
        return None, None, None, None


def render():
    """Render the ML Failure Prediction page."""
    st.markdown('<h1>🧠 ML Failure Prediction</h1>', unsafe_allow_html=True)
    st.markdown(
        "An experimental machine-learning predictor that estimates the probability "
        "that a PII placeholder will fail (be dropped, modified, or corrupted) during LLM processing."
    )

    st.warning(
        "⚠️ **EXPERIMENTAL MODULE**: This model is trained on synthetic scenario labels "
        "derived from documented failure rates, not from real LLM outputs. "
        "Results are **indicative only** and should not be used for production decisions."
    )

    predict_fn, predict_batch_fn, train_fn, get_meta_fn = _load_predictor()

    if predict_fn is None:
        st.error("Failure predictor module could not be loaded. Check `evaluation/failure_predictor.py`.")
        return

    # ── Model Status ────────────────────────────────────────────────────
    meta = get_meta_fn()
    model_path = PROJECT_ROOT / "evaluation" / "models" / "failure_predictor.pkl"

    st.markdown("---")
    st.markdown("#### 📦 Model Status")

    if meta.get("status") in ("trained", "loaded_existing") and model_path.exists():
        col1, col2, col3, col4 = st.columns(4)
        bm = meta.get("best_model_metrics", {})
        with col1:
            st.metric("Best Model", meta.get("best_model", "N/A"))
        with col2:
            st.metric("Accuracy", f"{bm.get('accuracy', 0)*100:.1f}%")
        with col3:
            st.metric("F1 Score", f"{bm.get('f1', 0)*100:.1f}%")
        with col4:
            st.metric("Train Samples", meta.get("train_samples", "N/A"))

        with st.expander("📋 Full Model Report"):
            lr = meta.get("logistic_regression", {})
            rf = meta.get("random_forest", {})
            comp_df = pd.DataFrame([
                {"Model": "Logistic Regression (Baseline)", **{k: f"{v*100:.1f}%" if isinstance(v, float) else v for k, v in lr.items() if k != "confusion_matrix"}},
                {"Model": "Random Forest", **{k: f"{v*100:.1f}%" if isinstance(v, float) else v for k, v in rf.items() if k != "confusion_matrix"}},
            ])
            st.dataframe(comp_df, use_container_width=True, hide_index=True)

            top_feat = meta.get("top_features", {})
            if top_feat:
                fig_feat = px.bar(
                    x=list(top_feat.values()), y=list(top_feat.keys()),
                    orientation="h", template="plotly_dark",
                    title="Top 10 Feature Importances",
                    labels={"x": "Importance", "y": "Feature"}
                )
                fig_feat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig_feat, use_container_width=True)

            st.info(meta.get("data_limitation", ""))
    else:
        st.info("Model not yet trained. Click 'Train Model' below.")

    if st.button("🔄 (Re-)Train Model", type="secondary"):
        with st.spinner("Training model on synthetic benchmark data..."):
            result = train_fn(force_retrain=True)
        if result.get("status") in ("trained",):
            st.success(f"✅ Model trained: {result.get('best_model')} | F1: {result.get('best_model_metrics', {}).get('f1', 0)*100:.1f}%")
            st.rerun()
        else:
            st.error(f"Training failed: {result.get('message', result)}")

    st.markdown("---")

    # ── Interactive Single Prediction ───────────────────────────────────
    st.markdown("#### 🎯 Interactive Failure Risk Predictor")
    st.markdown("Adjust the parameters below to estimate failure risk for a specific scenario.")

    c1, c2, c3 = st.columns(3)
    with c1:
        entity_type = st.selectbox("Entity Type", [
            "PERSON", "EMAIL", "PHONE", "LOCATION", "DATE",
            "ADDRESS", "IDENTIFICATION_NUMBER", "ORGANIZATION"
        ])
        strategy = st.selectbox("Placeholder Strategy", [
            "strategy_a_basic", "strategy_b_random_typed",
            "strategy_c_opaque", "strategy_d_protected"
        ], format_func=lambda x: {
            "strategy_a_basic": "A: Basic [PERSON_1]",
            "strategy_b_random_typed": "B: Random [PERSON_X7K92]",
            "strategy_c_opaque": "C: Opaque ZXQ7K92M",
            "strategy_d_protected": "D: Protected [PROT:...]",
        }.get(x, x))
    with c2:
        scenario = st.selectbox("LLM Scenario", [
            "normal", "paraphrase", "summarize", "translate",
            "grammar", "placeholder_modification",
            "placeholder_deletion", "placeholder_duplication"
        ], format_func=lambda x: x.replace("_", " ").title())
        pii_density = st.selectbox("PII Density", ["Low", "Medium", "High"])
    with c3:
        language = st.selectbox("Language", ["English", "Hinglish"])
        num_entities = st.slider("# Entities in Prompt", 1, 10, 3)
        token_count = st.slider("Prompt Token Count", 10, 150, 50)

    if st.button("🔮 Predict Failure Risk", type="primary"):
        result = predict_fn(
            entity_type=entity_type,
            placeholder_strategy=strategy,
            scenario=scenario,
            num_entities_in_prompt=num_entities,
            entity_index=0,
            pii_density=pii_density,
            language=language,
            prompt_token_count=token_count,
        )

        risk = result["risk_level"]
        prob = result["failure_probability"] * 100
        risk_colors = {"LOW": "#10b981", "MODERATE": "#f59e0b", "HIGH": "#ef4444", "VERY HIGH": "#dc2626", "UNKNOWN": "#64748b"}
        color = risk_colors.get(risk, "#64748b")

        st.markdown(f"""
        <div style="background:#111638; border:2px solid {color}; border-radius:12px; padding:20px; text-align:center; margin-top:12px;">
            <div style="font-size:2.5rem; font-weight:700; color:{color};">{prob:.1f}%</div>
            <div style="font-size:1.1rem; color:#f8fafc; margin-top:4px;">Predicted Failure Probability</div>
            <div style="font-size:1.3rem; font-weight:600; color:{color}; margin-top:8px;">Risk Level: {risk}</div>
            <div style="font-size:0.85rem; color:#94a3b8; margin-top:8px;">
                Prediction: <b>{result['prediction']}</b> |
                Entity: {entity_type} |
                Strategy: {strategy}
            </div>
            <div style="font-size:0.72rem; color:#64748b; margin-top:10px; font-style:italic;">
                ⚠️ EXPERIMENTAL — Synthetic labels only
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Batch Analysis of Current Session ───────────────────────────────
    st.markdown("#### 📊 Batch Risk Analysis for Current Pipeline Session")

    entities = st.session_state.get("entities", [])
    if not entities:
        st.info("💡 Run PII Detection first on the **🔍 PII Detection & Masking** page, then come back here for a risk assessment of your current prompt.")
    else:
        cur_strategy = st.session_state.get("placeholder_strategy", "strategy_a_basic")
        cur_scenario_key = st.session_state.get("llm_scenario", "normal")

        entity_types = [getattr(e, "entity_type", "OTHER") for e in entities]
        prompt_text = st.session_state.get("original_text", "")
        tok_count = len(prompt_text.split()) if prompt_text else 50

        preds = predict_batch_fn(
            entity_types=entity_types,
            placeholder_strategy=cur_strategy,
            scenario=cur_scenario_key,
            num_entities_in_prompt=len(entity_types),
            prompt_token_count=tok_count,
        )

        rows = []
        for et, p in zip(entity_types, preds):
            rows.append({
                "Entity Type": et,
                "Strategy": cur_strategy,
                "Scenario": cur_scenario_key,
                "Failure Prob": f"{p['failure_probability']*100:.1f}%",
                "Risk Level": p["risk_level"],
                "Prediction": p["prediction"],
            })
        df_batch = pd.DataFrame(rows)

        # Color risk column
        def risk_color(val):
            colors = {"LOW": "color: #10b981", "MODERATE": "color: #f59e0b",
                     "HIGH": "color: #ef4444", "VERY HIGH": "color: #dc2626"}
            return colors.get(val, "")

        st.dataframe(df_batch, use_container_width=True, hide_index=True)

        risk_counts = df_batch["Risk Level"].value_counts()
        if not risk_counts.empty:
            fig_risk = px.pie(
                names=risk_counts.index, values=risk_counts.values,
                color=risk_counts.index,
                color_discrete_map={"LOW": "#10b981", "MODERATE": "#f59e0b",
                                    "HIGH": "#ef4444", "VERY HIGH": "#dc2626"},
                title=f"Risk Distribution ({len(entities)} entities)",
                hole=0.4, template="plotly_dark"
            )
            fig_risk.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig_risk, use_container_width=True)

    st.markdown("---")

    # ── Scenario Risk Heatmap ────────────────────────────────────────────
    st.markdown("#### 🗺️ Scenario × Strategy Risk Heatmap (All Entity Types Averaged)")
    st.caption("Shows estimated failure probability for each scenario/strategy combination across all entity types.")

    strategies = ["strategy_a_basic", "strategy_b_random_typed", "strategy_c_opaque", "strategy_d_protected"]
    scenarios = ["normal", "paraphrase", "summarize", "translate", "grammar",
                 "placeholder_modification", "placeholder_deletion", "placeholder_duplication"]
    entity_types_all = ["PERSON", "EMAIL", "PHONE", "LOCATION", "DATE", "ADDRESS", "IDENTIFICATION_NUMBER"]

    @st.cache_data(show_spinner=False)
    def _compute_heatmap():
        hmap = {}
        for strat in strategies:
            hmap[strat] = {}
            for sc in scenarios:
                probs = []
                for et in entity_types_all:
                    p = predict_fn(
                        entity_type=et, placeholder_strategy=strat, scenario=sc,
                        num_entities_in_prompt=3, entity_index=0,
                        pii_density="Medium", language="English", prompt_token_count=50
                    )
                    probs.append(p["failure_probability"])
                hmap[strat][sc] = round(sum(probs) / len(probs) * 100, 1)
        return hmap

    if model_path.exists():
        with st.spinner("Computing heatmap..."):
            hmap = _compute_heatmap()

        strat_labels = {
            "strategy_a_basic": "A: Basic",
            "strategy_b_random_typed": "B: Random",
            "strategy_c_opaque": "C: Opaque",
            "strategy_d_protected": "D: Protected",
        }
        sc_labels = [s.replace("_", " ").title() for s in scenarios]
        z_data = [[hmap[s][sc] for sc in scenarios] for s in strategies]

        fig_heat = go.Figure(data=go.Heatmap(
            z=z_data,
            x=sc_labels,
            y=[strat_labels[s] for s in strategies],
            colorscale="RdYlGn_r",
            text=[[f"{v:.1f}%" for v in row] for row in z_data],
            texttemplate="%{text}",
            colorbar=dict(title="Failure %"),
        ))
        fig_heat.update_layout(
            title="Average Predicted Failure Probability (%) — Scenario × Strategy",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=350
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("🔴 Red = higher failure risk. 🟢 Green = lower risk. All values are EXPERIMENTAL estimates.")
    else:
        st.info("Train the model first to generate the risk heatmap.")


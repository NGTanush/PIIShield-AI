"""
Page: Research Dataset Explorer & Benchmark Suite
Allows viewing, inspecting, filtering, and launching experiments directly from the synthetic dataset.
Includes Public Dataset Benchmark tab (Kaggle pii-detection-removal-from-educational-data).
"""
import streamlit as st
import pandas as pd
import json
import os
import plotly.express as px
import plotly.graph_objects as go
from dashboard.styles import metric_card, data_panel, highlight_placeholders, status_badge
from detection.pii_detector import PIIEntity

DATASET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dataset")
PUBLIC_BENCHMARK_DIR = os.path.join(DATASET_DIR, "public_benchmark")


@st.cache_data
def load_dataset_files():
    """Load dataset files with caching."""
    prompts_csv = os.path.join(DATASET_DIR, "synthetic_prompts.csv")
    gt_json = os.path.join(DATASET_DIR, "ground_truth.json")
    scenarios_csv = os.path.join(DATASET_DIR, "experiment_scenarios.csv")
    variants_csv = os.path.join(DATASET_DIR, "placeholder_variants.csv")
    meta_json = os.path.join(DATASET_DIR, "dataset_metadata.json")

    prompts_df = pd.read_csv(prompts_csv) if os.path.exists(prompts_csv) else pd.DataFrame()
    scenarios_df = pd.read_csv(scenarios_csv) if os.path.exists(scenarios_csv) else pd.DataFrame()
    variants_df = pd.read_csv(variants_csv) if os.path.exists(variants_csv) else pd.DataFrame()

    ground_truth = []
    if os.path.exists(gt_json):
        with open(gt_json, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

    metadata = {}
    if os.path.exists(meta_json):
        with open(meta_json, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    return prompts_df, ground_truth, scenarios_df, variants_df, metadata


@st.cache_data
def load_kaggle_benchmark_data():
    """Load all Kaggle public benchmark files with caching."""
    meta_path = os.path.join(PUBLIC_BENCHMARK_DIR, "metadata", "kaggle_metadata.json")
    bench_path = os.path.join(PUBLIC_BENCHMARK_DIR, "results", "detection_benchmark_results.json")
    summary_csv_path = os.path.join(PUBLIC_BENCHMARK_DIR, "results", "detection_benchmark_summary.csv")
    per_cat_csv_path = os.path.join(PUBLIC_BENCHMARK_DIR, "results", "per_category_comparison.csv")
    download_info_path = os.path.join(PUBLIC_BENCHMARK_DIR, "metadata", "download_info.json")

    metadata = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

    benchmark_results = {}
    if os.path.exists(bench_path):
        with open(bench_path, "r", encoding="utf-8") as f:
            benchmark_results = json.load(f)

    summary_df = pd.read_csv(summary_csv_path) if os.path.exists(summary_csv_path) else pd.DataFrame()
    per_cat_df = pd.read_csv(per_cat_csv_path) if os.path.exists(per_cat_csv_path) else pd.DataFrame()

    download_info = {}
    if os.path.exists(download_info_path):
        with open(download_info_path, "r", encoding="utf-8") as f:
            download_info = json.load(f)

    return metadata, benchmark_results, summary_df, per_cat_df, download_info



def render():
    """Render the Research Dataset page."""
    st.markdown('<h1>📚 Research Dataset Explorer</h1>', unsafe_allow_html=True)
    st.markdown(
        "A rigorous, multi-scenario synthetic benchmark dataset for evaluating "
        "PII placeholder preservation and restoration fidelity in masked LLM pipelines."
    )

    prompts_df, ground_truth, scenarios_df, variants_df, metadata = load_dataset_files()

    if prompts_df.empty or not ground_truth:
        st.error("Dataset files not found in `dataset/`. Please run `python dataset/generate_dataset.py` first.")
        return

    # ── 1. Top Summary Metrics ──────────────────────────────────────────────
    st.markdown('<div class="section-header"><h3>📊 Benchmark Characteristics</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(metric_card("📝", "Total Prompts", metadata.get("total_prompts", len(prompts_df)), "blue"), unsafe_allow_html=True)
    with col2:
        st.markdown(metric_card("🏷️", "PII Entities", metadata.get("total_entities", "169"), "violet"), unsafe_allow_html=True)
    with col3:
        st.markdown(metric_card("📈", "Avg Density", f"{metadata.get('avg_entities_per_prompt', 2.8)}/prompt", "cyan"), unsafe_allow_html=True)
    with col4:
        st.markdown(metric_card("🧪", "Scenarios", len(metadata.get("scenario_distribution", {})), "green"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs for Navigation within Dataset Page ──────────────────────────────
    tab_browse, tab_inspect, tab_strategies, tab_analytics, tab_downloads, tab_public_benchmark = st.tabs([
        "📋 Browse Dataset",
        "🔍 Prompt Inspector & Runner",
        "🛡️ Placeholder Strategies (4 Variants)",
        "📈 Empirical Distributions",
        "📥 Data Downloads & Export",
        "🌐 Public Dataset Benchmark",
    ])


    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1: BROWSE DATASET
    # ─────────────────────────────────────────────────────────────────────────
    with tab_browse:
        st.markdown("##### Filter Benchmark Prompts")
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)

        with fcol1:
            all_scenarios = ["All"] + sorted(list(prompts_df["scenario"].unique()))
            sel_scenario = st.selectbox("Scenario", all_scenarios)
        with fcol2:
            all_densities = ["All"] + sorted(list(prompts_df["pii_density"].unique()))
            sel_density = st.selectbox("PII Density", all_densities)
        with fcol3:
            all_langs = ["All"] + sorted(list(prompts_df["language"].unique()))
            sel_lang = st.selectbox("Language", all_langs)
        with fcol4:
            entity_types = ["All", "PERSON", "EMAIL", "PHONE", "LOCATION", "DATE", "ADDRESS", "IDENTIFICATION_NUMBER"]
            sel_type = st.selectbox("Contains PII Type", entity_types)

        # Apply filters
        filtered_df = prompts_df.copy()
        if sel_scenario != "All":
            filtered_df = filtered_df[filtered_df["scenario"] == sel_scenario]
        if sel_density != "All":
            filtered_df = filtered_df[filtered_df["pii_density"] == sel_density]
        if sel_lang != "All":
            filtered_df = filtered_df[filtered_df["language"] == sel_lang]
        if sel_type != "All":
            filtered_df = filtered_df[filtered_df["pii_types"].str.contains(sel_type, na=False)]

        st.markdown(f"**Showing {len(filtered_df)} of {len(prompts_df)} synthetic prompts:**")

        display_cols = ["prompt_id", "original_prompt", "masked_prompt_basic", "num_entities", "pii_density", "language", "scenario"]
        st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2: PROMPT INSPECTOR & RUNNER
    # ─────────────────────────────────────────────────────────────────────────
    with tab_inspect:
        st.markdown("##### Detailed Prompt Inspection & Zero-Click Pipeline Execution")
        
        prompt_ids = [p["prompt_id"] for p in ground_truth]
        selected_id = st.selectbox("Select Prompt to Inspect:", prompt_ids, index=0)

        # Fetch ground truth item
        gt_item = next((item for item in ground_truth if item["prompt_id"] == selected_id), None)
        prompt_row = prompts_df[prompts_df["prompt_id"] == selected_id].iloc[0]

        if gt_item:
            # Metadata pills
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.markdown(f"**Language:** {status_badge(gt_item['language'], 'info')}", unsafe_allow_html=True)
            with m2:
                st.markdown(f"**Density:** {status_badge(gt_item['pii_density'], 'success' if gt_item['pii_density']=='Low' else 'warning')}", unsafe_allow_html=True)
            with m3:
                st.markdown(f"**Scenario:** {status_badge(gt_item['scenario'], 'violet' if hasattr(status_badge, 'violet') else 'info')}", unsafe_allow_html=True)
            with m4:
                st.markdown(f"**Entities:** `{gt_item['num_entities']}`", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col_orig, col_masked = st.columns(2)
            with col_orig:
                st.markdown("###### 📄 Original Prompt (Synthetic PII)")
                st.markdown(data_panel(gt_item["original_prompt"]), unsafe_allow_html=True)
            with col_masked:
                st.markdown("###### 🔒 Masked Prompt (Strategy A: Basic Placeholders)")
                st.markdown(data_panel(highlight_placeholders(prompt_row["masked_prompt_basic"])), unsafe_allow_html=True)

            # Ground Truth Annotations Table
            st.markdown("###### 🎯 Ground-Truth Entity Annotations (Character Offsets)")
            ann_data = []
            for a in gt_item["annotations"]:
                ann_data.append({
                    "Entity Type": a["entity_type"],
                    "Value": a["value"],
                    "Offsets (Start-End)": f"{a['start_char']} → {a['end_char']}",
                    "Strategy A (Basic)": a["placeholder_basic"],
                    "Strategy B (Random Typed)": a["placeholder_random_typed"],
                    "Strategy C (Opaque)": a["placeholder_opaque"],
                    "Strategy D (Protected)": a["placeholder_protected"]
                })
            st.dataframe(pd.DataFrame(ann_data), use_container_width=True, hide_index=True)

            # Execution button
            st.markdown("---")
            run_col1, run_col2, run_col3 = st.columns([2, 1, 1])
            with run_col1:
                st.info("💡 **Pipeline Integration**: Select a strategy and load this benchmark prompt directly into PIIShield AI's live masking and restoration workflow.")
            with run_col2:
                strat_options = {
                    "Strategy A (Basic)": "strategy_a_basic",
                    "Strategy B (Random Typed)": "strategy_b_random_typed",
                    "Strategy C (Opaque)": "strategy_c_opaque",
                    "Strategy D (Protected)": "strategy_d_protected"
                }
                load_strat_label = st.selectbox("Load with Strategy:", list(strat_options.keys()))
                load_strat_key = strat_options[load_strat_label]
            with run_col3:
                if st.button("🚀 Load into Live Pipeline", type="primary", use_container_width=True):
                    # Load into session state
                    st.session_state["original_text"] = gt_item["original_prompt"]
                    
                    strat_masked_map = {
                        "strategy_a_basic": prompt_row.get("masked_prompt_basic", ""),
                        "strategy_b_random_typed": prompt_row.get("strategy_b_random_typed_masked", prompt_row.get("masked_prompt_basic", "")),
                        "strategy_c_opaque": prompt_row.get("strategy_c_opaque_masked", prompt_row.get("masked_prompt_basic", "")),
                        "strategy_d_protected": prompt_row.get("strategy_d_protected_masked", prompt_row.get("masked_prompt_basic", ""))
                    }
                    st.session_state["masked_text"] = strat_masked_map.get(load_strat_key, prompt_row.get("masked_prompt_basic", ""))
                    st.session_state["placeholder_mapping"] = gt_item["strategy_mappings"].get(load_strat_key, gt_item["strategy_mappings"]["strategy_a_basic"])
                    st.session_state["placeholder_strategy"] = load_strat_key
                    st.session_state["data_provenance"] = "benchmark"
                    st.session_state["llm_scenario"] = gt_item["scenario"].lower().replace(" ", "_")

                    # Convert annotations to PIIEntity objects
                    detected_entities = []
                    for a in gt_item["annotations"]:
                        detected_entities.append(PIIEntity(
                            entity_type=a["entity_type"],
                            value=a["value"],
                            start=a["start_char"],
                            end=a["end_char"],
                            score=1.0,
                            source="ground_truth_dataset"
                        ))
                    st.session_state["entities"] = detected_entities
                    st.session_state["detection_done"] = True
                    st.session_state["llm_done"] = False
                    st.session_state["validation_done"] = False
                    st.session_state.pop("llm_response", None)
                    st.session_state.pop("validation_report", None)
                    st.session_state.pop("restored_text", None)
                    st.success(f"✅ Loaded `{selected_id}` ({load_strat_label}) into session! Navigate to **🤖 LLM Processing** or **🔍 PII Detection**.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3: PLACEHOLDER STRATEGIES COMPARISON
    # ─────────────────────────────────────────────────────────────────────────
    with tab_strategies:
        st.markdown("##### Four Experimental Placeholder Strategies")
        st.markdown(
            "To evaluate how placeholder representation affects LLM survival and downstream restoration, "
            "the dataset defines four distinct masking strategies:"
        )

        strat_cols = st.columns(4)
        with strat_cols[0]:
            st.markdown("""
            <div style="background: #111638; border: 1px solid #1e2a5a; border-radius: 12px; padding: 16px;">
                <h4 style="color: #3b82f6; margin-top:0;">Strategy A: Basic</h4>
                <p style="color: #94a3b8; font-size: 0.85rem;">Sequential typed tokens.</p>
                <code style="color: #c4b5fd;">[PERSON_1]</code><br>
                <code style="color: #c4b5fd;">[EMAIL_1]</code>
                <p style="color: #64748b; font-size: 0.75rem; margin-top: 8px;">Baseline standard; readable by LLM.</p>
            </div>
            """, unsafe_allow_html=True)
        with strat_cols[1]:
            st.markdown("""
            <div style="background: #111638; border: 1px solid #1e2a5a; border-radius: 12px; padding: 16px;">
                <h4 style="color: #8b5cf6; margin-top:0;">Strategy B: Random Typed</h4>
                <p style="color: #94a3b8; font-size: 0.85rem;">Typed with alphanumeric salt.</p>
                <code style="color: #c4b5fd;">[PERSON_X7K92]</code><br>
                <code style="color: #c4b5fd;">[EMAIL_M4N81]</code>
                <p style="color: #64748b; font-size: 0.75rem; margin-top: 8px;">Prevents index confusion & reuse collisions.</p>
            </div>
            """, unsafe_allow_html=True)
        with strat_cols[2]:
            st.markdown("""
            <div style="background: #111638; border: 1px solid #1e2a5a; border-radius: 12px; padding: 16px;">
                <h4 style="color: #06b6d4; margin-top:0;">Strategy C: Opaque</h4>
                <p style="color: #94a3b8; font-size: 0.85rem;">Zero semantic type leakage.</p>
                <code style="color: #c4b5fd;">ZXQ7K92M</code><br>
                <code style="color: #c4b5fd;">AB81J29L</code>
                <p style="color: #64748b; font-size: 0.75rem; margin-top: 8px;">Hides entity type completely from external LLM.</p>
            </div>
            """, unsafe_allow_html=True)
        with strat_cols[3]:
            st.markdown("""
            <div style="background: #111638; border: 1px solid #1e2a5a; border-radius: 12px; padding: 16px;">
                <h4 style="color: #10b981; margin-top:0;">Strategy D: Protected</h4>
                <p style="color: #94a3b8; font-size: 0.85rem;">Cryptographic checksum token.</p>
                <code style="color: #c4b5fd;">[PROT:PERSON:P1:C4D9]</code><br>
                <code style="color: #c4b5fd;">[PROT:EMAIL:P1:9F2A]</code>
                <p style="color: #64748b; font-size: 0.75rem; margin-top: 8px;">Cryptographically verifiable integrity tag.</p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("###### Multi-Strategy Masking Comparison Table")
        st.dataframe(variants_df.head(20), use_container_width=True, hide_index=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4: EMPIRICAL DISTRIBUTIONS
    # ─────────────────────────────────────────────────────────────────────────
    with tab_analytics:
        st.markdown("##### Dataset Distributions & Research Analytics")

        c1, c2 = st.columns(2)
        with c1:
            # PII Categories Bar Chart
            ec = metadata.get("entity_category_counts", {})
            if ec:
                fig1 = px.bar(
                    x=list(ec.keys()), y=list(ec.values()),
                    labels={"x": "Entity Category", "y": "Count"},
                    title="PII Entity Category Distribution",
                    color=list(ec.keys()),
                    template="plotly_dark"
                )
                fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
                st.plotly_chart(fig1, use_container_width=True)
        with c2:
            # Scenario Distribution
            sd = metadata.get("scenario_distribution", {})
            if sd:
                fig2 = px.pie(
                    names=list(sd.keys()), values=list(sd.values()),
                    title="Experimental Scenario Distribution",
                    hole=0.4,
                    template="plotly_dark"
                )
                fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
                st.plotly_chart(fig2, use_container_width=True)

        # Show static high-res distribution image if available
        chart_img_path = os.path.join(DATASET_DIR, "dataset_distribution.png")
        if os.path.exists(chart_img_path):
            st.markdown("###### 🖼️ High-Resolution Benchmark Architecture & Distribution Diagram")
            st.image(chart_img_path, caption="Comprehensive Dataset Empirical Profile (Generated via Matplotlib)", use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5: DOWNLOADS & EXPORTS
    # ─────────────────────────────────────────────────────────────────────────
    with tab_downloads:
        st.markdown("##### Download Research Benchmark Assets")
        st.markdown(
            "All generated synthetic assets can be exported directly for external analysis, "
            "paper reproduction, or benchmarking with alternative models."
        )

        dcol1, dcol2 = st.columns(2)
        with dcol1:
            csv_path_prompts = os.path.join(DATASET_DIR, "synthetic_prompts.csv")
            if os.path.exists(csv_path_prompts):
                with open(csv_path_prompts, "rb") as f:
                    st.download_button(
                        label="📥 Download synthetic_prompts.csv",
                        data=f,
                        file_name="synthetic_prompts.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            csv_path_scenarios = os.path.join(DATASET_DIR, "experiment_scenarios.csv")
            if os.path.exists(csv_path_scenarios):
                with open(csv_path_scenarios, "rb") as f:
                    st.download_button(
                        label="📥 Download experiment_scenarios.csv",
                        data=f,
                        file_name="experiment_scenarios.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

        with dcol2:
            json_path_gt = os.path.join(DATASET_DIR, "ground_truth.json")
            if os.path.exists(json_path_gt):
                with open(json_path_gt, "rb") as f:
                    st.download_button(
                        label="📥 Download ground_truth.json",
                        data=f,
                        file_name="ground_truth.json",
                        mime="application/json",
                        use_container_width=True
                    )

            csv_path_variants = os.path.join(DATASET_DIR, "placeholder_variants.csv")
            if os.path.exists(csv_path_variants):
                with open(csv_path_variants, "rb") as f:
                    st.download_button(
                        label="📥 Download placeholder_variants.csv",
                        data=f,
                        file_name="placeholder_variants.csv",
                        mime="text/csv",
                        use_container_width=True
                    )


    # ─────────────────────────────────────────────────────────────────────────
    # TAB 6: PUBLIC DATASET BENCHMARK (Kaggle)
    # ─────────────────────────────────────────────────────────────────────────
    with tab_public_benchmark:
        kag_meta, kag_bench, kag_summary_df, kag_per_cat_df, kag_dl_info = load_kaggle_benchmark_data()

        st.markdown("##### 🌐 Public Dataset Benchmark: Kaggle PII Detection")
        st.info(
            "**Research Separation Notice:** This benchmark evaluates **PII Detection** accuracy "
            "(Regex vs spaCy NER) against the public Kaggle competition dataset. "
            "It is **independent** of the synthetic dataset, which evaluates placeholder restoration fidelity. "
            "Detection metrics here reflect real-world detection capability, not round-trip restoration."
        )

        # ── Kaggle Auth / Download Status ───────────────────────────────────
        dl_status = kag_dl_info.get("status", "not_attempted")
        if dl_status == "success":
            st.success(
                f"✅ **Kaggle Dataset Downloaded**: {kag_dl_info.get('total_files', 0)} file(s) in "
                f"`dataset/public_benchmark/raw/`"
            )
        elif dl_status == "unauthenticated":
            st.warning(
                "⚠️ **Kaggle Dataset: Authentication Required**  \n"
                "The full competition dataset (6,807 student essays) requires a Kaggle API token.  \n"
                "**To unlock the full dataset:**  \n"
                "1. Log in at [kaggle.com](https://www.kaggle.com) and accept the [competition rules]"
                f"(https://www.kaggle.com/competitions/pii-detection-removal-from-educational-data/rules)  \n"
                "2. Go to **Account Settings → API → Create New Token** to download `kaggle.json`  \n"
                "3. Place it at: `C:\\Users\\tanus\\.kaggle\\kaggle.json`  \n"
                "4. Run: `python dataset/public_benchmark/download_kaggle.py`  \n\n"
                "**Currently running on 10-document representative sample** (same schema, same labels)."
            )
        else:
            st.info(
                "ℹ️ **Running on representative 10-document sample** with full Kaggle BIO annotation schema. "
                "To download the full 6,807-essay competition dataset, see the instructions above."
            )

        st.markdown("---")

        if not kag_meta:
            st.error("Public benchmark metadata not found. Run `python dataset/public_benchmark/preprocess_kaggle.py` first.")
        else:
            # ── Dataset Summary Metrics ────────────────────────────────────
            st.markdown("###### 📊 Dataset Summary")
            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(metric_card("📄", "Documents", kag_meta.get("total_documents", 0), "blue"), unsafe_allow_html=True)
            with m2:
                st.markdown(metric_card("🏷️", "Total Entities", kag_meta.get("total_entities", 0), "violet"), unsafe_allow_html=True)
            with m3:
                st.markdown(metric_card("🔤", "Total Tokens", kag_meta.get("total_tokens", 0), "cyan"), unsafe_allow_html=True)
            with m4:
                st.markdown(metric_card("⚠️", "PII Tokens", kag_meta.get("total_pii_tokens", 0), "orange"), unsafe_allow_html=True)
            with m5:
                pct = round(100 * kag_meta.get("total_pii_tokens", 0) / max(kag_meta.get("total_tokens", 1), 1), 1)
                st.markdown(metric_card("📐", "PII Density", f"{pct}%", "green"), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Entity Type Distribution ───────────────────────────────────
            cat1, cat2 = st.columns(2)
            with cat1:
                st.markdown("###### 🏷️ Ground-Truth PII Category Distribution")
                dist = kag_meta.get("entity_type_distribution", {})
                if dist:
                    fig_cat = px.bar(
                        x=list(dist.keys()),
                        y=list(dist.values()),
                        labels={"x": "Entity Type", "y": "Count"},
                        color=list(dist.keys()),
                        template="plotly_dark",
                        title="Kaggle Benchmark: Entity Categories"
                    )
                    fig_cat.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        showlegend=False, margin=dict(t=40, b=0)
                    )
                    st.plotly_chart(fig_cat, use_container_width=True)

            with cat2:
                st.markdown("###### 🏷️ Raw BIO Label Distribution")
                raw_dist = kag_meta.get("raw_bio_distribution", {})
                # Only B- tags for entity count
                b_dist = {k: v for k, v in raw_dist.items() if k.startswith("B-")}
                if b_dist:
                    fig_bio = px.pie(
                        names=[k.replace("B-", "") for k in b_dist.keys()],
                        values=list(b_dist.values()),
                        hole=0.4,
                        template="plotly_dark",
                        title="BIO Entity Start Tags"
                    )
                    fig_bio.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=40, b=0)
                    )
                    st.plotly_chart(fig_bio, use_container_width=True)

            st.markdown("---")

            # ── Detection Method Comparison ────────────────────────────────
            if kag_bench:
                st.markdown("###### ⚔️ PII Detection Method Comparison (Entity-Level, Exact Span Match)")

                method_labels = {
                    "regex": "1. Regex Patterns",
                    "spacy": "2. spaCy NER",
                    "hybrid": "3. Hybrid (Regex + NER)"
                }
                colors = {
                    "regex": "#3b82f6",
                    "spacy": "#8b5cf6",
                    "hybrid": "#10b981"
                }

                # Summary comparison cards
                bcol1, bcol2, bcol3 = st.columns(3)
                for col, (mkey, mlabel) in zip([bcol1, bcol2, bcol3], method_labels.items()):
                    if mkey in kag_bench:
                        res = kag_bench[mkey]
                        with col:
                            f1_pct = int(res["f1_score"] * 100)
                            p_pct = int(res["precision"] * 100)
                            r_pct = int(res["recall"] * 100)
                            best = mkey == "regex"  # regex has best precision
                            border_color = "#10b981" if best else "#1e2a5a"
                            st.markdown(f"""
                            <div style="background:#111638; border:2px solid {colors[mkey]};
                                        border-radius:12px; padding:16px; text-align:center;">
                                <div style="font-size:1rem; font-weight:600; color:{colors[mkey]}; margin-bottom:8px;">
                                    {mlabel}
                                </div>
                                <div style="font-size:2rem; font-weight:700; color:#f8fafc;">{f1_pct}%</div>
                                <div style="font-size:0.75rem; color:#94a3b8;">Micro F1</div>
                                <div style="margin-top:8px; display:flex; justify-content:space-around;">
                                    <span style="font-size:0.8rem; color:#3b82f6;">P: {p_pct}%</span>
                                    <span style="font-size:0.8rem; color:#8b5cf6;">R: {r_pct}%</span>
                                </div>
                                <div style="margin-top:6px; font-size:0.72rem; color:#64748b;">
                                    TP: {res["true_positives"]} | FP: {res["false_positives"]} | FN: {res["false_negatives"]}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Visual comparison chart
                methods_display = [method_labels[m] for m in ["regex", "spacy", "hybrid"]]
                metrics_fig = go.Figure()
                for metric_name, metric_key, color in [
                    ("Precision", "precision", "#3b82f6"),
                    ("Recall", "recall", "#8b5cf6"),
                    ("F1 Score", "f1_score", "#10b981"),
                ]:
                    vals = [kag_bench[m][metric_key] * 100 for m in ["regex", "spacy", "hybrid"]]
                    metrics_fig.add_trace(go.Bar(
                        name=metric_name,
                        x=methods_display,
                        y=vals,
                        marker_color=color,
                        text=[f"{v:.1f}%" for v in vals],
                        textposition="outside"
                    ))
                metrics_fig.update_layout(
                    barmode="group",
                    template="plotly_dark",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    title="Detection Method Comparison (Exact Span Matching)",
                    yaxis=dict(title="Score (%)", range=[0, 110]),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02),
                    margin=dict(t=60, b=20)
                )
                st.plotly_chart(metrics_fig, use_container_width=True)

                st.markdown("---")

                # ── Per-Category Breakdown ─────────────────────────────────
                st.markdown("###### 📋 Per-Category Performance Breakdown")
                if not kag_per_cat_df.empty:
                    styled_df = kag_per_cat_df.copy()
                    # Format as percentages
                    for col in ["Precision", "Recall", "F1_Score"]:
                        if col in styled_df.columns:
                            styled_df[col] = styled_df[col].apply(lambda x: f"{x*100:.1f}%")
                    st.dataframe(styled_df, use_container_width=True, hide_index=True)

                    # Heatmap: F1 by method and category
                    pivot_data = []
                    for mkey in ["regex", "spacy", "hybrid"]:
                        if mkey in kag_bench:
                            for cat, cdata in kag_bench[mkey]["per_category"].items():
                                pivot_data.append({
                                    "Method": method_labels[mkey],
                                    "Entity_Type": cat,
                                    "F1": cdata["f1_score"] * 100
                                })
                    if pivot_data:
                        df_pivot = pd.DataFrame(pivot_data).pivot(
                            index="Entity_Type", columns="Method", values="F1"
                        ).fillna(0)
                        fig_heat = px.imshow(
                            df_pivot,
                            text_auto=".1f",
                            color_continuous_scale="Blues",
                            title="F1 Score Heatmap: Method × Entity Type (%)",
                            template="plotly_dark",
                            aspect="auto"
                        )
                        fig_heat.update_layout(
                            paper_bgcolor="rgba(0,0,0,0)",
                            plot_bgcolor="rgba(0,0,0,0)",
                            margin=dict(t=50, b=20)
                        )
                        st.plotly_chart(fig_heat, use_container_width=True)

                st.markdown("---")

                # ── Findings & Limitations ─────────────────────────────────
                st.markdown("###### 🔬 Key Findings & Methodology Notes")
                regex_f1 = kag_bench.get("regex", {}).get("f1_score", 0) * 100
                hybrid_f1 = kag_bench.get("hybrid", {}).get("f1_score", 0) * 100
                spacy_f1 = kag_bench.get("spacy", {}).get("f1_score", 0) * 100
                best_method = max(
                    [("Regex", regex_f1), ("Hybrid", hybrid_f1), ("spaCy NER", spacy_f1)],
                    key=lambda x: x[1]
                )
                st.markdown(f"""
                <div style="background:#111638; border:1px solid #1e2a5a; border-radius:12px; padding:16px;">
                    <p style="color:#f8fafc; margin:0 0 10px 0;"><b>Best performing method:</b>
                        <span style="color:#10b981;">{best_method[0]} ({best_method[1]:.1f}% F1)</span>
                    </p>
                    <ul style="color:#94a3b8; font-size:0.85rem; padding-left:18px; margin:0;">
                        <li><b>Regex</b> achieves highest precision ({kag_bench.get('regex',{}).get('precision',0)*100:.1f}%) on EMAIL (100%) and PHONE, but misses PERSON, ADDRESS, and URL entirely due to lack of NER capability.</li>
                        <li><b>spaCy NER</b> captures some PERSON entities but generates many false positives, lowering precision to {kag_bench.get('spacy',{}).get('precision',0)*100:.1f}%.</li>
                        <li><b>Hybrid (Regex + NER)</b> achieves the best recall ({kag_bench.get('hybrid',{}).get('recall',0)*100:.1f}%) by combining both methods, but false positives from spaCy reduce overall precision.</li>
                        <li><b>Important:</b> Exact span matching is strict — multi-token entities (e.g., "450 University Way, Seattle, WA 98105") must match character-for-character to count as a true positive.</li>
                        <li><b>Limitation:</b> This benchmark uses {kag_meta.get("total_documents", 10)} representative sample documents. The full Kaggle dataset (6,807 essays) requires Kaggle API authentication.</li>
                        <li><b>Research Scope:</b> These metrics reflect <em>detection</em> accuracy only. Placeholder restoration fidelity is evaluated separately on the synthetic dataset.</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

            # ── Category Mapping Reference ─────────────────────────────────
            with st.expander("📌 Kaggle Label → PIIShield Type Mapping"):
                cat_map = kag_meta.get("category_mapping", {})
                mapping_df = pd.DataFrame([
                    {"Kaggle BIO Label": f"B-{k} / I-{k}", "PIIShield Standard Type": v}
                    for k, v in cat_map.items()
                ])
                st.dataframe(mapping_df, use_container_width=True, hide_index=True)

            # ── CSV Export Buttons ─────────────────────────────────────────
            st.markdown("---")
            st.markdown("###### 📥 Export Benchmark Results")
            ecol1, ecol2 = st.columns(2)
            with ecol1:
                summary_path = os.path.join(PUBLIC_BENCHMARK_DIR, "results", "detection_benchmark_summary.csv")
                if os.path.exists(summary_path):
                    with open(summary_path, "rb") as f:
                        st.download_button(
                            label="📥 Download detection_benchmark_summary.csv",
                            data=f,
                            file_name="detection_benchmark_summary.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                per_cat_path = os.path.join(PUBLIC_BENCHMARK_DIR, "results", "per_category_comparison.csv")
                if os.path.exists(per_cat_path):
                    with open(per_cat_path, "rb") as f:
                        st.download_button(
                            label="📥 Download per_category_comparison.csv",
                            data=f,
                            file_name="per_category_comparison.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            with ecol2:
                gt_csv_path = os.path.join(PUBLIC_BENCHMARK_DIR, "processed", "kaggle_processed.csv")
                if os.path.exists(gt_csv_path):
                    with open(gt_csv_path, "rb") as f:
                        st.download_button(
                            label="📥 Download kaggle_processed.csv (Ground Truth Spans)",
                            data=f,
                            file_name="kaggle_processed.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                bench_json_path = os.path.join(PUBLIC_BENCHMARK_DIR, "results", "detection_benchmark_results.json")
                if os.path.exists(bench_json_path):
                    with open(bench_json_path, "rb") as f:
                        st.download_button(
                            label="📥 Download detection_benchmark_results.json",
                            data=f,
                            file_name="detection_benchmark_results.json",
                            mime="application/json",
                            use_container_width=True
                        )

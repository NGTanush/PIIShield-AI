"""Page 4: Placeholder Validation and PII Restoration."""
import streamlit as st
import pandas as pd
from validation.placeholder_validator import validate_placeholders, FailureCategory
from restoration.pii_restorer import PIIRestorer
from dashboard.styles import (
    metric_card, data_panel, highlight_placeholders, status_badge
)


def render():
    """Render the Validation & Restoration page."""
    st.markdown('<h1>🔐 Validation & Restoration</h1>', unsafe_allow_html=True)
    st.markdown("Validate placeholder integrity and restore PII in verified placeholders only.")
    
    # Check prerequisites
    if not st.session_state.get("llm_done"):
        st.warning("⚠️ Please complete **LLM Processing** first.")
        return
    
    llm_response = st.session_state.get("llm_response", "")
    mapping = st.session_state.get("placeholder_mapping", {})
    masked_text = st.session_state.get("masked_text", "")
    
    # ── Raw LLM Response ──────────────────────────────────
    st.markdown('<div class="section-header"><h3>📥 Raw LLM Response</h3></div>',
                 unsafe_allow_html=True)
    
    mode_label = st.session_state.get("llm_mode", "unknown")
    if "demo" in mode_label:
        st.warning("⚠️ This response is **simulated** (demo mode).")
    
    highlighted = highlight_placeholders(llm_response.replace("<", "&lt;").replace(">", "&gt;"))
    st.markdown(data_panel(highlighted), unsafe_allow_html=True)
    
    # ── Validate ──────────────────────────────────────────
    if st.button("🔎 Validate & Restore", type="primary", use_container_width=True):
        with st.spinner("Validating placeholders..."):
            report = validate_placeholders(llm_response, mapping, masked_text)
        
        # Store for evaluation
        st.session_state["validation_report"] = report
        
        # Summary metrics
        st.markdown('<div class="section-header"><h3>📊 Validation Summary</h3></div>',
                     unsafe_allow_html=True)
        
        summary = report.summary()
        cols = st.columns(4)
        with cols[0]:
            st.markdown(metric_card("✅", "Correct", summary["correct"], "green"),
                         unsafe_allow_html=True)
        with cols[1]:
            st.markdown(metric_card("❌", "Dropped", summary["dropped"], "red"),
                         unsafe_allow_html=True)
        with cols[2]:
            st.markdown(metric_card("⚠️", "Inflected", summary["inflected"], "amber"),
                         unsafe_allow_html=True)
        with cols[3]:
            st.markdown(
                metric_card("👻", "Hallucinated", summary["hallucinated"], "violet"),
                unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        cols2 = st.columns(4)
        with cols2[0]:
            st.markdown(metric_card("🔀", "Cross-wired", summary["cross_wired"], "cyan"),
                         unsafe_allow_html=True)
        with cols2[1]:
            st.markdown(metric_card("🌐", "Mistranslated", summary["mistranslated"], "blue"),
                         unsafe_allow_html=True)
        with cols2[2]:
            st.markdown(metric_card("👁️", "Missed", summary["missed"], "amber"),
                         unsafe_allow_html=True)
        with cols2[3]:
            st.markdown(metric_card("📋", "Duplicated", summary["duplicated"], "red"),
                         unsafe_allow_html=True)
        
        # ── Per-placeholder details ───────────────────────
        st.markdown('<div class="section-header"><h3>📋 Per-Placeholder Results</h3></div>',
                     unsafe_allow_html=True)
        
        result_data = []
        for r in report.results:
            cat = r.category.value
            result_data.append({
                "Placeholder": r.placeholder,
                "Status": cat.upper(),
                "Found As": r.found_text or "—",
                "Notes": r.notes,
            })
        
        st.dataframe(pd.DataFrame(result_data), use_container_width=True, hide_index=True)
        
        if report.unexpected_placeholders:
            st.markdown("**Hallucinated Placeholders** (not in original prompt):")
            for ph in report.unexpected_placeholders:
                st.markdown(f"- `{ph}`")
        
        if report.duplicate_placeholders:
            st.markdown("**Duplicated Placeholders:**")
            for ph in report.duplicate_placeholders:
                st.markdown(f"- `{ph}`")
        
        # ── Restoration ───────────────────────────────────
        st.markdown('<div class="section-header"><h3>🔓 PII Restoration</h3></div>',
                     unsafe_allow_html=True)
        
        st.info("🔒 **Strict Privacy Rule**: Only **CORRECT** placeholders are restored. Failed or ambiguous placeholders are left un-restored to prevent leaking wrong data.")
        
        restorer = PIIRestorer()
        restored_text, log = restorer.restore(llm_response, mapping, report)
        
        st.session_state["restored_text"] = restored_text
        st.session_state["restoration_log"] = log
        st.session_state["validation_done"] = True
        
        # Show restored text
        st.markdown("##### Restored Response")
        st.markdown(data_panel(
            restored_text.replace("<", "&lt;").replace(">", "&gt;")
        ), unsafe_allow_html=True)
        
        # Restoration log
        with st.expander("📝 Restoration Log", expanded=False):
            log_data = []
            for entry in log:
                log_data.append({
                    "Placeholder": entry["placeholder"],
                    "Status": entry["status"],
                    "Restored Value": entry.get("restored_value", "—"),
                    "Notes": entry.get("notes", ""),
                })
            st.dataframe(pd.DataFrame(log_data), use_container_width=True, hide_index=True)
        
        st.success("✅ Validation and restoration complete! Proceed to **Research Evaluation**.")
    
    elif st.session_state.get("validation_done"):
        st.info("✅ Previous validation results available. Proceed to **Research Evaluation** or re-validate.")


"""Page: About the Research — Methodology, Threat Model, Architecture & Limitations."""
import streamlit as st


def render():
    """Render the About the Research page."""
    st.markdown('<h1>📖 About PIIShield AI Research</h1>', unsafe_allow_html=True)
    st.markdown(
        "**Research Project:** *Privacy-Preserving NLP: Round-Trip Fidelity Evaluation "
        "of PII Restoration in Masked LLM Prompting Pipelines*"
    )

    # ── Executive Abstract ──────────────────────────────────────────────
    st.markdown("""
    <div style="background: #111638; border-left: 4px solid #3b82f6; padding: 18px; border-radius: 8px; margin: 15px 0;">
        <h4 style="color: #60a5fa; margin-top:0;">📄 Research Abstract</h4>
        <p style="color: #cbd5e1; font-size: 0.92rem; line-height: 1.6; margin: 0;">
            Large Language Models (LLMs) deployed as third-party cloud APIs present severe privacy risks when handling 
            personally identifiable information (PII). While pseudonymization via placeholder tokens is widely proposed, 
            prior literature lacks rigorous quantitative evaluation of <b>round-trip restoration fidelity</b> — whether 
            placeholders survive complex LLM syntactic transformations intact, and whether original sensitive values 
            can be reconstructed downstream without identity leakage. 
            <b>PIIShield AI</b> establishes an empirical evaluation framework comprising 300 benchmark prompts across 
            852 verified PII entities, four distinct placeholder strategies, seven failure classification modes, 
            and a zero-leakage conditional restoration engine.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Threat Model & Privacy Guarantees ───────────────────────────────
    st.markdown('<div class="section-header"><h3>🛡️ Threat Model & Security Boundaries</h3></div>', unsafe_allow_html=True)

    tcol1, tcol2 = st.columns(2)
    with tcol1:
        st.markdown("""
        <div style="background: #111638; border: 1px solid #1e2a5a; border-radius: 12px; padding: 18px;">
            <h4 style="color: #10b981; margin-top:0;">🔒 What PIIShield Guarantees</h4>
            <ul style="color: #94a3b8; font-size: 0.85rem; padding-left: 18px; line-height: 1.6;">
                <li><b>Zero Remote Transmission:</b> Raw PII entities are stripped locally on the client host before network transmission.</li>
                <li><b>Isolated Local Mapping:</b> The dictionary binding placeholders to plaintexts never leaves local memory.</li>
                <li><b>Strict Conditional Restoration:</b> Tokens are restored <i>if and only if</i> they pass structural and cryptographic validation.</li>
                <li><b>No Guessing:</b> Dropped, corrupted, or hallucinated tokens are never guessed or substituted.</li>
                <li><b>Sanitized Experiment Logging:</b> Database records contain only masked tokens and metrics, never raw sensitive values.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with tcol2:
        st.markdown("""
        <div style="background: #111638; border: 1px solid #1e2a5a; border-radius: 12px; padding: 18px;">
            <h4 style="color: #f59e0b; margin-top:0;">⚠️ Known Security & Privacy Limitations</h4>
            <ul style="color: #94a3b8; font-size: 0.85rem; padding-left: 18px; line-height: 1.6;">
                <li><b>Contextual Re-identification:</b> Masking specific identifiers (e.g. name, email) does not prevent quasi-identifier linkage (e.g., "the 44th US President born in Hawaii").</li>
                <li><b>Detection Imperfection:</b> Unrecognized PII entities by the NER/Regex layer may escape masking.</li>
                <li><b>Not Differential Privacy:</b> Placeholder masking is syntactic pseudonymization, not mathematical differential privacy ($\\epsilon, \\delta$).</li>
                <li><b>Adversarial Semantic Probing:</b> Sophisticated prompts could cause an LLM to infer masked context from surrounding tokens.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Mathematical Metrics Framework ─────────────────────────────────
    st.markdown('<div class="section-header"><h3>📐 Mathematical Metric Definitions</h3></div>', unsafe_allow_html=True)

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.markdown("##### 1. Restoration Precision ($P_{rest}$)")
        st.latex(r"P_{rest} = \frac{\text{Correct Restorations}}{\text{Total Restoration Attempts}} = \frac{TP_{rest}}{TP_{rest} + FP_{rest}}")
        st.caption("Measures what fraction of restored tokens were restored accurately without corruption or cross-wiring.")

        st.markdown("##### 2. Restoration Recall ($R_{rest}$)")
        st.latex(r"R_{rest} = \frac{\text{Correct Restorations}}{\text{Total Expected Placeholders}} = \frac{TP_{rest}}{\text{Total Expected}}")
        st.caption("Measures what fraction of original PII placeholders successfully survived the round-trip pipeline.")

    with mcol2:
        st.markdown("##### 3. Restoration F1 Score ($F_1$)")
        st.latex(r"F_1 = \frac{2 \cdot P_{rest} \cdot R_{rest}}{P_{rest} + R_{rest}}")
        st.caption("Harmonic mean balancing precision and recall. Correctly penalizes dropped tokens and invalid restorations.")

        st.markdown("##### 4. Placeholder Preservation Rate")
        st.latex(r"\text{Preservation Rate} = \frac{\text{Total Expected} - \text{Dropped}}{\text{Total Expected}}")
        st.caption("Fraction of placeholders preserved in any form by the LLM (including inflected or modified tokens).")

    st.markdown("---")

    # ── Seven Failure Categories ────────────────────────────────────────
    st.markdown('<div class="section-header"><h3>🔍 The Seven Failure Categories</h3></div>', unsafe_allow_html=True)

    fail_categories = [
        {"Category": "CORRECT", "Code": "0x00", "Description": "Token preserved perfectly; passes structural and cryptographic checks.", "Restoration Action": "RESTORE"},
        {"Category": "MISSED", "Code": "0x01", "Description": "Placeholder replaced by LLM with a generic noun phrase ('the client').", "Restoration Action": "SKIP (Unrestored)"},
        {"Category": "DROPPED", "Code": "0x02", "Description": "Token completely deleted from LLM output.", "Restoration Action": "SKIP (Unrestored)"},
        {"Category": "INFLECTED", "Code": "0x03", "Description": "Token altered in format (brackets stripped, lowercase, parentheses).", "Restoration Action": "BLOCK (Unrestored)"},
        {"Category": "MISTRANSLATED", "Code": "0x04", "Description": "Token identifier translated into foreign language ([PERSONNE_1]).", "Restoration Action": "BLOCK (Unrestored)"},
        {"Category": "HALLUCINATED", "Code": "0x05", "Description": "Spurious placeholder created by LLM with no local mapping.", "Restoration Action": "REJECT"},
        {"Category": "CROSS_WIRED", "Code": "0x06", "Description": "Multiple placeholders swapped positions or entity bindings.", "Restoration Action": "BLOCK"},
    ]
    st.dataframe(fail_categories, use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Research System Summary ─────────────────────────────────────────
    st.markdown('<div class="section-header"><h3>🏢 Implementation Specifications</h3></div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
        **Pipeline Stack:**
        - **Frontend:** Streamlit 1.28+
        - **Visualization:** Plotly Dark & Matplotlib
        - **Data Handling:** Pandas, NumPy
        - **Storage:** SQLite 3 (Sanitized)
        """)
    with c2:
        st.markdown("""
        **NLP & ML Stack:**
        - **NER Engine:** spaCy 3.8 (`en_core_web_sm`)
        - **Pattern Matching:** Regex PII Suite
        - **ML Classifier:** Scikit-learn (Logistic Regression & Random Forest)
        - **Public Benchmark:** Kagglehub
        """)
    with c3:
        st.markdown("""
        **Security Features:**
        - Isolated local mapping dictionaries
        - Multi-strategy entropy masking
        - Cryptographic CRC checksums
        - Test isolation sandboxing
        """)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("💡 **Academic Citation:** PIIShield AI Research Team, *'Privacy-Preserving NLP: Round-Trip Fidelity Evaluation of PII Restoration in Masked LLM Prompting Pipelines'*, College Final Year Project, 2026.")

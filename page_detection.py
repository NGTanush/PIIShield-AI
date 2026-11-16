"""Page 2: PII Detection and Masking."""
import streamlit as st
import pandas as pd
from detection.pii_detector import detect_pii
from masking.pii_masker import PIIMasker
from dashboard.styles import metric_card, data_panel, highlight_placeholders, status_badge

SAMPLE_TEXTS = {
    "Sample 1 - Basic Contact": (
        "My name is Rahul Sharma. My email is rahul@example.com "
        "and my phone number is +91-9876543210."
    ),
    "Sample 2 - Dual Entity (Hinglish)": (
        "Mera naam Amit Kumar hai. Priya Verma se 9876543210 par call karke "
        "confirm kar lo ki meeting kal 15/08/2025 ko MG Road Bengaluru me hogi."
    ),
    "Sample 3 - Rich Patient Record": (
        "Patient: Dr. Sanjay Gupta\n"
        "DOB: January 5, 1985\n"
        "Email: sanjay.gupta@hospital.org\n"
        "Phone: +1-555-0142\n"
        "Address: 200 Wellness Blvd, New York\n"
        "SSN: 123-45-6789\n"
        "Emergency contact: Neha Gupta, neha.g@email.com"
    ),
    "Sample 4 - Financial & Tax Identifiers": (
        "Client Rahul Sharma (PAN: ABCDE1234F, Aadhaar: 4532 8901 2345) "
        "requested tax statement dispatched to 42 MG Road, Bengaluru."
    ),
    "Custom Text": "",
}

STRATEGY_MAP = {
    "Strategy A: Basic Typed ([PERSON_1])": "strategy_a_basic",
    "Strategy B: Random Typed ([PERSON_X7K92])": "strategy_b_random_typed",
    "Strategy C: Opaque Random (ZXQ7K92M)": "strategy_c_opaque",
    "Strategy D: Protected Checksum ([PROT:PERSON:P1:C4D9])": "strategy_d_protected"
}


def render():
    """Render the PII Detection & Masking page."""
    st.markdown('<h1>🔍 PII Detection & Masking</h1>', unsafe_allow_html=True)
    st.markdown("Enter text containing synthetic PII to detect and mask personal information.")
    
    # ── Text input ────────────────────────────────────────
    st.markdown('<div class="section-header"><h3>📝 Input Text & Configuration</h3></div>', unsafe_allow_html=True)
    
    loaded_prompt = st.session_state.get("original_text", "")
    sample_options = list(SAMPLE_TEXTS.keys())
    if loaded_prompt and "📌 Loaded from Research Dataset" not in sample_options:
        sample_options.insert(0, "📌 Loaded from Research Dataset")

    sample_choice = st.selectbox("Choose a sample or enter custom text:", sample_options)
    
    if sample_choice == "📌 Loaded from Research Dataset":
        default_text = loaded_prompt
    else:
        default_text = SAMPLE_TEXTS.get(sample_choice, "")
    
    text_input = st.text_area(
        "Enter text with synthetic PII:",
        value=default_text,
        height=160,
        placeholder="Type or paste text containing names, emails, phone numbers, identifiers, etc."
    )
    
    col_cfg1, col_cfg2 = st.columns(2)
    with col_cfg1:
        strategy_label = st.selectbox(
            "Select Placeholder Masking Strategy:",
            list(STRATEGY_MAP.keys()),
            index=0
        )
        selected_strategy = STRATEGY_MAP[strategy_label]

    with col_cfg2:
        use_spacy = st.checkbox("Use spaCy NER (for names, locations, organizations)", value=True)
        st.caption("Structured identifiers (Email, Phone, Date, SSN, PAN, Aadhaar) are recognized via deterministic regex.")

    if st.button("🔍 Detect & Mask PII", type="primary", use_container_width=True):
        if not text_input.strip():
            st.warning("Please enter some text first.")
            return
        
        # Detect PII
        with st.spinner("Detecting PII entities..."):
            entities = detect_pii(text_input, use_spacy=use_spacy)
        
        if not entities:
            st.warning("No PII entities detected. Try a different sample or add names, emails, etc.")
            return
        
        # Mask PII with selected strategy
        masker = PIIMasker(strategy=selected_strategy)
        masked_text, mapping = masker.mask_text(text_input, entities)
        
        # Store in session state for next pages
        st.session_state["original_text"] = text_input
        st.session_state["entities"] = entities
        st.session_state["masked_text"] = masked_text
        st.session_state["placeholder_mapping"] = mapping
        st.session_state["placeholder_strategy"] = selected_strategy
        st.session_state["detection_done"] = True
        # Reset downstream pipeline states on fresh detection/masking
        st.session_state["llm_done"] = False
        st.session_state["validation_done"] = False
        st.session_state.pop("llm_response", None)
        st.session_state.pop("validation_report", None)
        st.session_state.pop("restored_text", None)
        
        # ── Results ───────────────────────────────────────
        st.markdown('<div class="section-header"><h3>📊 Detection & Masking Results</h3></div>',
                     unsafe_allow_html=True)
        
        # Metrics
        cols = st.columns(4)
        with cols[0]:
            st.markdown(metric_card("🔍", "Entities Found", len(entities), "violet"),
                         unsafe_allow_html=True)
        with cols[1]:
            types = set(e.entity_type for e in entities)
            st.markdown(metric_card("🏷️", "Entity Types", len(types), "cyan"),
                         unsafe_allow_html=True)
        with cols[2]:
            st.markdown(metric_card("🔒", "Placeholders", len(mapping), "green"),
                         unsafe_allow_html=True)
        with cols[3]:
            st.markdown(metric_card("🛡️", "Strategy", selected_strategy.split("_")[-1].capitalize(), "blue"),
                         unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Original vs Masked
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("##### 📄 Original Text (Local Only)")
            st.markdown(data_panel(text_input.replace("<", "&lt;").replace(">", "&gt;")),
                         unsafe_allow_html=True)
        
        with col_right:
            st.markdown(f"##### 🔒 Masked Text ({strategy_label.split(':')[0]})")
            highlighted = highlight_placeholders(
                masked_text.replace("<", "&lt;").replace(">", "&gt;")
            )
            st.markdown(data_panel(highlighted), unsafe_allow_html=True)
        
        # Entity table
        st.markdown('<div class="section-header"><h3>📋 Detected Entities (Ground Truth Candidate)</h3></div>',
                     unsafe_allow_html=True)
        
        entity_data = []
        for e in entities:
            entity_data.append({
                "Entity Type": e.entity_type,
                "Detected Value": e.value,
                "Confidence": f"{e.score:.0%}",
                "Source Layer": e.source,
                "Character Span": f"{e.start} → {e.end}",
            })
        
        st.dataframe(pd.DataFrame(entity_data), use_container_width=True, hide_index=True)
        
        # Placeholder mapping
        st.markdown('<div class="section-header"><h3>🗺️ Isolated Local Mapping</h3></div>',
                     unsafe_allow_html=True)
        
        mapping_data = [{"Placeholder": k, "Original Value": v} for k, v in mapping.items()]
        st.dataframe(pd.DataFrame(mapping_data), use_container_width=True, hide_index=True)
        
        st.success("✅ PII detected and masked! Proceed to **🤖 LLM Processing**.")
    
    elif st.session_state.get("detection_done"):
        st.info("✅ Active masked text ready in session. Proceed to **🤖 LLM Processing** or re-mask with another strategy.")

"""LLM Processing module with demo mode, Ollama, and optional API integration."""
import os
import json
import re
import random
from typing import Dict, Optional, Tuple


# ── Demo / simulated responses ────────────────────────────────────────
DEMO_SCENARIOS = {
    "normal": {
        "name": "Normal Response",
        "description": "LLM preserves all placeholders exactly as given.",
        "transform": lambda text: _demo_normal(text),
    },
    "paraphrase": {
        "name": "Paraphrasing",
        "description": "LLM paraphrases the text but keeps placeholders.",
        "transform": lambda text: _demo_paraphrase(text),
    },
    "summarize": {
        "name": "Summarization",
        "description": "LLM summarizes the text, keeping placeholders.",
        "transform": lambda text: _demo_summarize(text),
    },
    "translate": {
        "name": "Translation",
        "description": "LLM translates surrounding text to French; may alter placeholder format.",
        "transform": lambda text: _demo_translate(text),
    },
    "grammar": {
        "name": "Grammar Correction",
        "description": "LLM corrects grammar, placeholders should survive.",
        "transform": lambda text: _demo_grammar(text),
    },
    "placeholder_modification": {
        "name": "Placeholder Modification",
        "description": "LLM modifies placeholder format (e.g., removes brackets).",
        "transform": lambda text: _demo_modify_placeholder(text),
    },
    "placeholder_deletion": {
        "name": "Placeholder Deletion",
        "description": "LLM drops some placeholders entirely from the response.",
        "transform": lambda text: _demo_delete_placeholder(text),
    },
    "placeholder_duplication": {
        "name": "Placeholder Duplication",
        "description": "LLM duplicates a placeholder in the response.",
        "transform": lambda text: _demo_duplicate_placeholder(text),
    },
}


def _find_placeholders(text: str):
    """Return list of all placeholders across Strategies A, B, C, and D."""
    from validation.placeholder_validator import find_all_placeholders
    return find_all_placeholders(text)


def _demo_normal(text: str) -> str:
    prefix = "Based on the information provided, here is my response:\n\n"
    return prefix + text


def _demo_paraphrase(text: str) -> str:
    result = text
    swaps = [
        ("My name is", "I am"),
        ("My email is", "You can reach me at"),
        ("my phone number is", "my contact number is"),
        ("I live at", "My residence is"),
        ("I was born on", "My date of birth is"),
    ]
    for old, new in swaps:
        result = result.replace(old, new)
    return "Here is the paraphrased version:\n\n" + result


def _demo_summarize(text: str) -> str:
    placeholders = _find_placeholders(text)
    if not placeholders:
        return "Summary: " + text[:200]
    parts = []
    for ph in placeholders:
        ptype = ph.strip("[]").rsplit("_", 1)[0]
        parts.append(f"{ptype}: {ph}")
    return "Summary of provided information:\n" + "\n".join(parts)


def _demo_translate(text: str) -> str:
    """Simulate translation - keep some placeholders, mistranslate one."""
    result = text
    translations = {
        "My name is": "Mon nom est",
        "My email is": "Mon email est",
        "my phone number is": "mon numéro de téléphone est",
        "I live at": "J'habite à",
    }
    for eng, fra in translations.items():
        result = result.replace(eng, fra)
    
    # Simulate mistranslation of a placeholder
    placeholders = _find_placeholders(result)
    if placeholders:
        victim = placeholders[0]
        # Change bracket style to simulate mistranslation
        broken = victim.replace("[", "(").replace("]", ")")
        result = result.replace(victim, broken, 1)
    
    return "Traduction:\n\n" + result


def _demo_grammar(text: str) -> str:
    return "Corrected text:\n\n" + text


def _demo_modify_placeholder(text: str) -> str:
    """Modify placeholder format to simulate LLM altering them."""
    result = text
    placeholders = _find_placeholders(text)
    if placeholders:
        # Modify first placeholder (remove brackets)
        victim = placeholders[0]
        modified = victim.strip("[]")
        result = result.replace(victim, modified, 1)
    
    if len(placeholders) > 1:
        # Lowercase another
        victim2 = placeholders[1]
        modified2 = victim2.lower()
        result = result.replace(victim2, modified2, 1)
    
    return "Processed response:\n\n" + result


def _demo_delete_placeholder(text: str) -> str:
    """Delete one or more placeholders."""
    result = text
    placeholders = _find_placeholders(text)
    if placeholders:
        # Remove the first placeholder
        victim = placeholders[0]
        result = result.replace(victim, "", 1)
        # Clean up double spaces
        result = re.sub(r'  +', ' ', result)
    return "Response:\n\n" + result


def _demo_duplicate_placeholder(text: str) -> str:
    """Duplicate a placeholder."""
    result = text
    placeholders = _find_placeholders(text)
    if placeholders:
        victim = placeholders[-1]
        result = result + f"\n\nNote: Please confirm that {victim} is correct. {victim} appears in our records."
    return result


def process_with_demo(masked_text: str, scenario: str = "normal") -> Tuple[str, str]:
    """
    Process masked text using demo/simulated mode.
    
    Returns:
        Tuple of (response_text, mode_label).
        mode_label is always 'demo (simulated)'.
    """
    if scenario not in DEMO_SCENARIOS:
        scenario = "normal"
    
    transformer = DEMO_SCENARIOS[scenario]["transform"]
    response = transformer(masked_text)
    
    return response, "demo (simulated)"


def process_with_ollama(masked_text: str, model: str = "llama3.2",
                        system_prompt: str = "") -> Tuple[str, str]:
    """
    Process masked text using a local Ollama instance.
    
    Returns:
        Tuple of (response_text, mode_label).
    """
    try:
        import requests
    except ImportError:
        return "Error: 'requests' package not installed.", "ollama (error)"
    
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    if not system_prompt:
        system_prompt = (
            "You are a helpful assistant. The user text contains placeholders "
            "like [PERSON_1], [EMAIL_1], etc. Preserve these placeholders exactly "
            "as they appear in your response. Do not modify, remove, or replace them."
        )
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": masked_text},
        ],
        "stream": False,
    }
    
    try:
        resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data.get("message", {}).get("content", "")
        return content, f"ollama ({model})"
    except requests.ConnectionError:
        return "Error: Could not connect to Ollama. Is it running?", "ollama (error)"
    except Exception as e:
        return f"Error: {str(e)}", "ollama (error)"


def process_with_api(masked_text: str, provider: str = "openai") -> Tuple[str, str]:
    """
    Process using an external API (OpenAI-compatible).
    Requires API key set in environment variables.
    
    Returns:
        Tuple of (response_text, mode_label).
    """
    api_key = os.getenv("LLM_API_KEY", "")
    api_base = os.getenv("LLM_API_BASE", "https://api.openai.com/v1")
    api_model = os.getenv("LLM_API_MODEL", "gpt-3.5-turbo")
    
    if not api_key:
        return "Error: LLM_API_KEY environment variable not set.", "api (error)"
    
    try:
        import requests
    except ImportError:
        return "Error: 'requests' package not installed.", "api (error)"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": api_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. The user text contains placeholders "
                    "like [PERSON_1], [EMAIL_1], etc. Preserve these placeholders exactly."
                ),
            },
            {"role": "user", "content": masked_text},
        ],
    }
    
    try:
        resp = requests.post(f"{api_base}/chat/completions",
                             headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content, f"api ({api_model})"
    except Exception as e:
        return f"Error: {str(e)}", "api (error)"


def get_available_scenarios() -> Dict[str, Dict]:
    """Return metadata for all demo scenarios."""
    return {k: {"name": v["name"], "description": v["description"]}
            for k, v in DEMO_SCENARIOS.items()}

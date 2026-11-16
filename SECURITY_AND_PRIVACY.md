# Security and Privacy Analysis: PIIShield AI

**Document:** Security & Privacy Specification  
**Project:** PIIShield AI — Privacy-Preserving NLP Middleware  
**Date:** November 2026  

---

## 1. Threat Model & Adversary Assumptions

PIIShield AI adopts a multi-party threat model reflecting realistic cloud LLM deployments:

```
[Local Client Trust Domain]             [Untrusted Network / Cloud Domain]
┌───────────────────────────────┐       ┌────────────────────────────────┐
│ User Terminal & Local Memory  │       │ Third-Party LLM Cloud Provider │
│                               │       │                                │
│ • Plaintext PII Entities      │       │ • Prompt Logging Infrastructure│
│ • Local Mapping Dictionary    │  REST │ • Model Memorization Pipelines │
│ • Cryptographic Secret / CRC  │──────►│ • Training Data Scraping       │
│ • Sanitized SQLite DB         │ (SSL) │                                │
│                               │       │ Adversary Model:               │
│ Threat Boundary: TRUSTED      │       │ HONEST-BUT-CURIOUS & UNTRUSTED │
└───────────────────────────────┘       └────────────────────────────────┘
```

### 1.1 Adversary Personas

1. **Honest-but-Curious Cloud Provider:** The LLM provider (or their downstream logging/telemetry pipelines) faithfully executes model inference, but stores, inspects, or uses input prompts for secondary purposes (e.g. model retraining, telemetry audit).
2. **Untrusted Eavesdropper:** An entity attempting passive interception on transit channels (mitigated by TLS/SSL transport and placeholder redaction).
3. **Malicious Prompt Injector / Token Mutator:** An adversarial actor attempting to modify placeholder tokens within prompt context to trick the downstream restorer into cross-wiring identities or injecting unauthorized strings into local applications.

---

## 2. Core Security Invariants

### Invariant 1: Zero Remote PII Transmission
* **Guarantee:** Plaintext PII entity values are stripped on the client host before network serialization.
* **Verification:** Network inspection confirms that only placeholder strings (e.g., `[PERSON_1]`, `ZXQ7K92M`, `[PROT:EMAIL:P1:9F2A]`) appear in HTTP request payloads to Ollama or remote OpenAI endpoints.

### Invariant 2: Isolated Local Memory Mapping
* **Guarantee:** The reverse translation dictionary:
  $$\mathcal{M} = \{ \tau_i \mapsto v_i \}$$
  resides exclusively in volatile process memory on the client machine.
* **Storage Invariant:** Plaintext dictionary $\mathcal{M}$ is never serialized to disk, transmitted over sockets, or written to SQLite experiment logs.

### Invariant 3: Strict Conditional Restoration
* **Guarantee:** A placeholder $\tau$ is restored if and only if:
  $$\tau \in \text{dom}(\mathcal{M}) \land \text{Category}(\tau) = \text{CORRECT} \land \text{Verify}(\tau) = \text{True}$$
* **Non-Restoration Rule:** Dropped, inflected, mistranslated, or hallucinated tokens are **never** restored with speculative identities.

---

## 3. Pseudonymization vs. Differential Privacy

A fundamental academic distinction must be maintained between **syntactic pseudonymization** and **formal differential privacy**:

| Dimension | PIIShield AI (Syntactic Pseudonymization) | Differential Privacy ($\epsilon, \delta$) |
| :--- | :--- | :--- |
| **Mechanism** | Deterministic token masking and client-side restoration. | Algorithmic noise injection (e.g., Laplace / Gaussian mechanisms). |
| **Privacy Unit** | Explicit PII named entities (Names, Emails, Phones, Addresses, IDs). | Bounded worst-case probability ratio on individual inclusion. |
| **Utility Impact** | **Near-Zero utility loss:** LLM retains full syntax and semantic context. | Significant utility degradation for nuanced language generation. |
| **Protection Scope**| Protects direct identifiers from direct cloud extraction. | Protects arbitrary statistical attributes from reconstruction attacks. |
| **Limitation** | Susceptible to contextual re-identification via quasi-identifiers. | Requires formal query boundaries; difficult for open-ended dialog. |

> **Crucial Disclaimer:** PIIShield AI **does not guarantee differential privacy**. It provides client-side pseudonymization and round-trip integrity verification.

---

## 4. Contextual Re-identification & Quasi-Identifier Risks

Masking direct identifiers (e.g., changing *"Dr. Anthony Fauci"* to `[PERSON_1]`) does not prevent an LLM from inferring the masked identity if the surrounding factual context contains unique **quasi-identifiers**:

* **Example:** *"In March 2020, `[PERSON_1]` served as Director of NIAID and advised the White House coronavirus task force."*
* **Inference Risk:** Any advanced LLM can deduce with high confidence that `[PERSON_1]` is Dr. Anthony Fauci.

### PIIShield AI Mitigation:
1. **Strategy C (Opaque Random):** Removes semantic entity category hints, reducing LLM attention bias toward specific biographical categories.
2. **Context Auditing (Recommendation):** Sensitive prompts should be pre-filtered for high-cardinality quasi-identifiers before external transmission.

---

## 5. Strategy D Cryptographic Checksum Analysis

Strategy D embeds a 4-character deterministic cryptographic checksum derived from the original plaintext value:

$$\text{Checksum}(\tau) = \text{MD5}(v)[:4].\text{upper}()$$

* **Entropy:** $16^4 = 65,536$ unique checksum combinations.
* **Collision Probability:** For typical prompt entity counts ($N \le 10$), the probability of an accidental random collision is:
  $$P(\text{Collision}) \approx 1 - \exp\left(-\frac{N^2}{2 \cdot 65536}\right) < 0.00076 \quad (0.076\%)$$
* **Tamper Resistance:** If an adversary mutates the placeholder index or entity type (e.g. from `[PROT:PERSON:P1:C4D9]` to `[PROT:PERSON:P2:C4D9]`), the checksum check detects the mismatch with 99.92% probability and blocks restoration.

---

## 6. Recommendations for Enterprise Production

For organizations deploying PIIShield AI in healthcare, legal, or financial production environments:

1. **Deploy in Ephemeral Micro-Gateways:** Run the middleware inside containerized sidecars (e.g. Envoy/Kubernetes sidecar) with strict memory isolation.
2. **Enable Strategy D for Adversarial Pipelines:** Always select Strategy D (Protected) when processing untrusted web content or agentic multi-tool workflows.
3. **Audit Local SQLite Storage:** Maintain database encryption at rest (`SQLCipher` or OS-level BitLocker) for `piishield.db`.
4. **Regular Regex & Model Updates:** Periodically refresh custom PII regex patterns to reflect regional identity formats (Aadhaar, NHS numbers, CPF, SSN).


"""
PIIShield AI — Research Dataset Generator (Expanded 300+ Benchmark Suite)

Generates a large-scale, multi-scenario synthetic dataset for evaluating
PII placeholder survival and round-trip restoration fidelity in LLM pipelines.

Outputs:
  - dataset/synthetic_prompts.csv
  - dataset/ground_truth.json
  - dataset/experiment_scenarios.csv
  - dataset/placeholder_variants.csv
  - dataset/dataset_metadata.json
  - dataset/dataset_summary.json
  - dataset/dataset_distribution.png
"""

import os
import sys
import io
import json
import csv
import random
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Force UTF-8 output encoding on Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set reproducible seed
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

DATASET_DIR = os.path.dirname(os.path.abspath(__file__))

# ─────────────────────────────────────────────────────────────────────────────
# 1. EXTENDED SYNTHETIC ENTITY POOLS (100% Artificial / Fictional)
# ─────────────────────────────────────────────────────────────────────────────

FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Neha", "Vikram", "Ananya", "Rohan", "Pooja",
    "Sanjay", "Kavita", "Arjun", "Sunita", "Deepak", "Shreya", "Rajesh", "Meera",
    "Karan", "Divya", "Suresh", "Tanvi", "Aditya", "Ritu", "Gaurav", "Sneha",
    "David", "Elena", "Marcus", "Sarah", "Chen", "Aisha", "Carlos", "Fatima",
    "Nikhil", "Swati", "Harish", "Pallavi", "Alok", "Rashmi", "Varun", "Isha",
    "Manish", "Bhavna", "Kunal", "Preeti", "Sameer", "Geeta", "Tushar", "Smita"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Kumar", "Singh", "Rao", "Nair",
    "Reddy", "Mehta", "Chopra", "Joshi", "Bose", "Das", "Deshmukh", "Iyer",
    "Thorne", "Vance", "Mercer", "Novak", "Kowalski", "Santos", "Morales", "Dubois",
    "Kulkarni", "Bhatia", "Aggarwal", "Banerjee", "Menon", "Saxena", "Pillai", "Pandey"
]

DOMAINS = [
    "testcorp.net", "syntheticmail.org", "fictionaldomain.edu", "sampleorg.co.in",
    "mockservice.io", "demomail.com", "dummycorp.org", "pseudoidentity.in",
    "shieldtest.ai", "datasafe.org", "sandboxmail.net", "researchlab.edu"
]

CITIES = [
    "Bengaluru", "Mumbai", "New Delhi", "Hyderabad", "Pune",
    "Chennai", "Kolkata", "Ahmedabad", "Jaipur", "Chandigarh",
    "Seattle", "London", "Singapore", "Berlin", "Toronto", "Sydney",
    "Indore", "Lucknow", "Kochi", "Bhopal", "Visakhapatnam", "Nagpur"
]

STREETS = [
    "42 MG Road", "15 Brigade Road", "88 Park Street", "102 Outer Ring Road",
    "23 Connaught Place", "56 Anna Salai", "78 FC Road", "14 Marine Drive",
    "67 Sector 18", "91 Indiranagar 100ft Road", "120 Cyber City Avenue",
    "34 Residency Road", "55 Hitech City Road", "77 Banjara Hills Road No 12",
    "89 Whitefield Main Road", "10 Kaloor Junction", "28 Gomti Nagar Marg"
]

DATES = [
    "15/08/2025", "24-11-2024", "January 14, 2025", "03/12/2024",
    "March 22, 2025", "10-10-2025", "August 5, 2024", "18/09/2025",
    "01/04/2025", "12-07-2024", "February 28, 2025", "19/11/2025",
    "May 30, 2025", "07-06-2024", "September 15, 2025", "31/12/2024"
]

# ─────────────────────────────────────────────────────────────────────────────
# 2. SEED TEMPLATES (DIVERSE STRUCTURES & ALL 7 PII CATEGORIES)
# ─────────────────────────────────────────────────────────────────────────────

BASE_PROMPT_SPECS = [
    # ── Single Entity (Low Density) ──────────────────────────────────────────
    {"template": "Please schedule the team follow-up call with {PERSON_1}.", "types": ["PERSON"], "lang": "English", "scenario": "Normal", "category": "Conversational"},
    {"template": "All project deliverables must be submitted to {EMAIL_1} by end of day.", "types": ["EMAIL"], "lang": "English", "scenario": "Grammar Correction", "category": "Directive"},
    {"template": "For emergency system escalations, dial {PHONE_1} immediately.", "types": ["PHONE"], "lang": "English", "scenario": "Normal", "category": "Support"},
    {"template": "Our new cloud research center is located in {LOCATION_1}.", "types": ["LOCATION"], "lang": "English", "scenario": "Summarization", "category": "Informational"},
    {"template": "The confidentiality agreement takes effect on {DATE_1}.", "types": ["DATE"], "lang": "English", "scenario": "Paraphrasing", "category": "Legal"},
    {"template": "Courier the signed physical forms to {ADDRESS_1}.", "types": ["ADDRESS"], "lang": "English", "scenario": "Normal", "category": "Logistics"},
    {"template": "Identity record verification failed for Aadhaar {AADHAAR_1}.", "types": ["IDENTIFICATION_NUMBER"], "lang": "English", "scenario": "Placeholder Modification", "category": "Compliance"},
    {"template": "Please ensure the client tax invoice includes PAN number {PAN_1}.", "types": ["IDENTIFICATION_NUMBER"], "lang": "English", "scenario": "Normal", "category": "Finance"},
    {"template": "Patient Social Security Number recorded as {SSN_1} in health records.", "types": ["IDENTIFICATION_NUMBER"], "lang": "English", "scenario": "Normal", "category": "Healthcare"},
    {"template": "Visa clearance issued for international passport {PASSPORT_1}.", "types": ["IDENTIFICATION_NUMBER"], "lang": "English", "scenario": "Normal", "category": "Immigration"},
    {"template": "Mera naam {PERSON_1} hai aur mujhe access issue ho raha hai.", "types": ["PERSON"], "lang": "Hinglish / Code-Mixed", "scenario": "Paraphrasing", "category": "Support"},
    {"template": "Agar query solve na ho toh {EMAIL_1} par ping kar dena please.", "types": ["EMAIL"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Conversational"},
    {"template": "Urgent verification ke liye {PHONE_1} par call lagao abhi.", "types": ["PHONE"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Support"},
    {"template": "Agla regional conference {LOCATION_1} mein organize hone wala hai.", "types": ["LOCATION"], "lang": "Hinglish / Code-Mixed", "scenario": "Summarization", "category": "Events"},
    {"template": "Final project review ki deadline {DATE_1} fix ki gayi hai.", "types": ["DATE"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Scheduling"},
    {"template": "Courier package ko {ADDRESS_1} par drop kar dena.", "types": ["ADDRESS"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Logistics"},

    # ── Dual & Triple Entity (Medium Density) ────────────────────────────────
    {"template": "My name is {PERSON_1} and my primary email address is {EMAIL_1}.", "types": ["PERSON", "EMAIL"], "lang": "English", "scenario": "Normal", "category": "Personal Profile"},
    {"template": "Please contact {PERSON_1} at {PHONE_1} regarding the architectural audit.", "types": ["PERSON", "PHONE"], "lang": "English", "scenario": "Paraphrasing", "category": "Enterprise"},
    {"template": "Dr. {PERSON_1} has relocated the consultation practice to {LOCATION_1}.", "types": ["PERSON", "LOCATION"], "lang": "English", "scenario": "Summarization", "category": "Medical"},
    {"template": "Mr. {PERSON_1} will join the executive board on {DATE_1}.", "types": ["PERSON", "DATE"], "lang": "English", "scenario": "Normal", "category": "Corporate"},
    {"template": "Send the invoice to {EMAIL_1} or call the billing desk at {PHONE_1}.", "types": ["EMAIL", "PHONE"], "lang": "English", "scenario": "Normal", "category": "Billing"},
    {"template": "The client meeting in {LOCATION_1} has been confirmed for {DATE_1}.", "types": ["LOCATION", "DATE"], "lang": "English", "scenario": "Translation", "category": "Scheduling"},
    {"template": "Deliver the medical supplies to {ADDRESS_1} before {DATE_1}.", "types": ["ADDRESS", "DATE"], "lang": "English", "scenario": "Normal", "category": "Logistics"},
    {"template": "Taxpayer {PERSON_1} holds PAN {PAN_1} registered in our corporate database.", "types": ["PERSON", "IDENTIFICATION_NUMBER"], "lang": "English", "scenario": "Normal", "category": "Finance"},
    {"template": "Aadhaar number {AADHAAR_1} belongs to account holder {PERSON_1}.", "types": ["IDENTIFICATION_NUMBER", "PERSON"], "lang": "English", "scenario": "Placeholder Deletion", "category": "Banking"},
    {"template": "{PERSON_1} lives in {LOCATION_1} and can be reached via {EMAIL_1}.", "types": ["PERSON", "LOCATION", "EMAIL"], "lang": "English", "scenario": "Normal", "category": "Directory"},
    {"template": "Please reach out to {PERSON_1} at {EMAIL_1} or on mobile {PHONE_1}.", "types": ["PERSON", "EMAIL", "PHONE"], "lang": "English", "scenario": "Normal", "category": "Contact"},
    {"template": "Patient {PERSON_1} visited our clinic in {LOCATION_1} on {DATE_1}.", "types": ["PERSON", "LOCATION", "DATE"], "lang": "English", "scenario": "Summarization", "category": "Healthcare"},
    {"template": "Shipment for {PERSON_1} has been dispatched to {ADDRESS_1} via courier.", "types": ["PERSON", "ADDRESS"], "lang": "English", "scenario": "Paraphrasing", "category": "E-Commerce"},
    {"template": "Applicant {PERSON_1} presented passport {PASSPORT_1} expiring on {DATE_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "DATE"], "lang": "English", "scenario": "Normal", "category": "Immigration"},
    {"template": "Employee {PERSON_1} has SSN {SSN_1} and primary contact {EMAIL_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "EMAIL"], "lang": "English", "scenario": "Normal", "category": "Human Resources"},
    {"template": "Aap {PERSON_1} se contact kar sakte hain unke email {EMAIL_1} par.", "types": ["PERSON", "EMAIL"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Conversational"},
    {"template": "{PERSON_1} ka mobile number {PHONE_1} hai, unhe kal message kardo.", "types": ["PERSON", "PHONE"], "lang": "Hinglish / Code-Mixed", "scenario": "Grammar Correction", "category": "Conversational"},
    {"template": "Meeting {LOCATION_1} me schedule hui hai on {DATE_1} morning 10 AM.", "types": ["LOCATION", "DATE"], "lang": "Hinglish / Code-Mixed", "scenario": "Paraphrasing", "category": "Scheduling"},
    {"template": "Mera PAN number {PAN_1} update kar dijiye for client {PERSON_1}.", "types": ["IDENTIFICATION_NUMBER", "PERSON"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Banking"},
    {"template": "Dr. {PERSON_1} ko urgent call karo at {PHONE_1} regarding report {DATE_1}.", "types": ["PERSON", "PHONE", "DATE"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Healthcare"},
    {"template": "{PERSON_1} ne bola tha ki {ADDRESS_1} par files courier kar do before {DATE_1}.", "types": ["PERSON", "ADDRESS", "DATE"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Logistics"},

    # ── Multiple Entities of Same Type (Disambiguation) ──────────────────────
    {"template": "Both {PERSON_1} and {PERSON_2} will represent the privacy engineering team.", "types": ["PERSON", "PERSON"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Team"},
    {"template": "{PERSON_1} assigned the cloud migration task to senior engineer {PERSON_2}.", "types": ["PERSON", "PERSON"], "lang": "English", "scenario": "Multiple Placeholder Confusion", "category": "Workflow"},
    {"template": "Send a copy to {EMAIL_1} as well as the backup mailbox {EMAIL_2}.", "types": ["EMAIL", "EMAIL"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Email Routing"},
    {"template": "You can reach customer support at either {PHONE_1} or alternate hotline {PHONE_2}.", "types": ["PHONE", "PHONE"], "lang": "English", "scenario": "Normal", "category": "Support"},
    {"template": "The flight departs from {LOCATION_1} and arrives at {LOCATION_2} in the afternoon.", "types": ["LOCATION", "LOCATION"], "lang": "English", "scenario": "Translation", "category": "Travel"},
    {"template": "The trial commenced on {DATE_1} and concluded successfully on {DATE_2}.", "types": ["DATE", "DATE"], "lang": "English", "scenario": "Summarization", "category": "Research"},
    {"template": "Project partners {PERSON_1}, {PERSON_2}, and {PERSON_3} attended the workshop.", "types": ["PERSON", "PERSON", "PERSON"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Collaboration"},
    {"template": "{PERSON_1} aur {PERSON_2} dono kal {LOCATION_1} ja rahe hain.", "types": ["PERSON", "PERSON", "LOCATION"], "lang": "Hinglish / Code-Mixed", "scenario": "Multi-Entity Processing", "category": "Travel"},
    {"template": "Donon emails {EMAIL_1} aur {EMAIL_2} par OTP check kar lena.", "types": ["EMAIL", "EMAIL"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Security"},
    {"template": "{PERSON_1} ne {PERSON_2} ko bataya ki {LOCATION_1} office open ho gaya hai.", "types": ["PERSON", "PERSON", "LOCATION"], "lang": "Hinglish / Code-Mixed", "scenario": "Multiple Placeholder Confusion", "category": "Conversational"},

    # ── High Density & Complex Multiplexed Prompts (4+ entities) ─────────────
    {"template": "Dear {PERSON_1}, thank you for registering with our clinic in {LOCATION_1}. Your contact number {PHONE_1} and email {EMAIL_1} have been verified for your appointment on {DATE_1}.", "types": ["PERSON", "LOCATION", "PHONE", "EMAIL", "DATE"], "lang": "English", "scenario": "Normal", "category": "Registration"},
    {"template": "Employee {PERSON_1} (Aadhaar: {AADHAAR_1}) transferred from {LOCATION_1} to {ADDRESS_1} on {DATE_1}. Official notification sent to {EMAIL_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "LOCATION", "ADDRESS", "DATE", "EMAIL"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Human Resources"},
    {"template": "Attention: {PERSON_1} and {PERSON_2} must verify their PAN numbers {PAN_1} and {PAN_2} before {DATE_1}. Contact audit desk at {EMAIL_1}.", "types": ["PERSON", "PERSON", "IDENTIFICATION_NUMBER", "IDENTIFICATION_NUMBER", "DATE", "EMAIL"], "lang": "English", "scenario": "Multiple Placeholder Confusion", "category": "Compliance"},
    {"template": "Patient record for {PERSON_1}: DOB {DATE_1}, emergency contact {PERSON_2} at phone {PHONE_1}, residing at {ADDRESS_1}, primary physician reachable at {EMAIL_1}.", "types": ["PERSON", "DATE", "PERSON", "PHONE", "ADDRESS", "EMAIL"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Healthcare Record"},
    {"template": "Purchase order for {PERSON_1}: Billing address {ADDRESS_1}, contact {PHONE_1}, delivery date {DATE_1}, order manager {PERSON_2} at {EMAIL_1}.", "types": ["PERSON", "ADDRESS", "PHONE", "DATE", "PERSON", "EMAIL"], "lang": "English", "scenario": "Normal", "category": "E-Commerce"},
    {"template": "Legal summons for {PERSON_1} residing at {ADDRESS_1}. Issued by attorney {PERSON_2} on {DATE_1}. Hearing in {LOCATION_1}. Inquiries: {EMAIL_1}.", "types": ["PERSON", "ADDRESS", "PERSON", "DATE", "LOCATION", "EMAIL"], "lang": "English", "scenario": "Summarization", "category": "Legal"},
    {"template": "Tax audit case: Taxpayer {PERSON_1} (SSN: {SSN_1}) and co-signer {PERSON_2} residing at {ADDRESS_1} requested review on {DATE_1}. Response directed to {EMAIL_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "PERSON", "ADDRESS", "DATE", "EMAIL"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Finance"},
    {"template": "International traveler {PERSON_1} holding passport {PASSPORT_1} arrived in {LOCATION_1} on {DATE_1}. Contact number is {PHONE_1} and local residence {ADDRESS_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "LOCATION", "DATE", "PHONE", "ADDRESS"], "lang": "English", "scenario": "Normal", "category": "Travel"},
    {"template": "{PERSON_1} ka account update ho gaya hai: Email {EMAIL_1}, phone {PHONE_1}, aur address {ADDRESS_1}. Verification date: {DATE_1}.", "types": ["PERSON", "EMAIL", "PHONE", "ADDRESS", "DATE"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Profile Update"},
    {"template": "Client {PERSON_1} and manager {PERSON_2} ne PAN {PAN_1} verify kiya on {DATE_1}. Confirmation email {EMAIL_1} par send kar diya.", "types": ["PERSON", "PERSON", "IDENTIFICATION_NUMBER", "DATE", "EMAIL"], "lang": "Hinglish / Code-Mixed", "scenario": "Multiple Placeholder Confusion", "category": "Banking"},
    {"template": "Aadhaar {AADHAAR_1} and mobile {PHONE_1} linking request submitted by {PERSON_1} at {LOCATION_1} branch on {DATE_1}. Update sent to {EMAIL_1}.", "types": ["IDENTIFICATION_NUMBER", "PHONE", "PERSON", "LOCATION", "DATE", "EMAIL"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Banking"},

    # ── Perturbation-Targeted Stress Prompts ─────────────────────────────────
    {"template": "Please confirm that customer {PERSON_1} with email {EMAIL_1} is approved for credit line activation.", "types": ["PERSON", "EMAIL"], "lang": "English", "scenario": "Placeholder Modification", "category": "Stress Test"},
    {"template": "Security notice: {PERSON_1} requested password reset from {LOCATION_1}. Verification link sent to {EMAIL_1}.", "types": ["PERSON", "LOCATION", "EMAIL"], "lang": "English", "scenario": "Placeholder Deletion", "category": "Security"},
    {"template": "Executive assistant {PERSON_1} scheduled the quarterly board briefing with {PERSON_2} for {DATE_1}.", "types": ["PERSON", "PERSON", "DATE"], "lang": "English", "scenario": "Placeholder Duplication", "category": "Corporate"},
    {"template": "Translate to French for our overseas team: Contact {PERSON_1} at {EMAIL_1} or visit {ADDRESS_1}.", "types": ["PERSON", "EMAIL", "ADDRESS"], "lang": "English", "scenario": "Translation", "category": "Multilingual"},
    {"template": "Correct all punctuation errors: Client {PERSON_1} mobile is {PHONE_1} and tax ID is {PAN_1} residing in {LOCATION_1}.", "types": ["PERSON", "PHONE", "IDENTIFICATION_NUMBER", "LOCATION"], "lang": "English", "scenario": "Grammar Correction", "category": "Syntax"},
    {"template": "Summarize this incident: System engineer {PERSON_1} detected an unauthorized login attempt from {LOCATION_1} on {DATE_1}. Incident log emailed to {EMAIL_1}.", "types": ["PERSON", "LOCATION", "DATE", "EMAIL"], "lang": "English", "scenario": "Summarization", "category": "Incident Response"},
    {"template": "Paraphrase politely: Customer {PERSON_1} must pay pending invoice before {DATE_1} or contact {PHONE_1}.", "types": ["PERSON", "DATE", "PHONE"], "lang": "English", "scenario": "Paraphrasing", "category": "Billing"},
    {"template": "{PERSON_1} aur {PERSON_2} ka ticket status check karke {EMAIL_1} par update forward kardo before {DATE_1}.", "types": ["PERSON", "PERSON", "EMAIL", "DATE"], "lang": "Hinglish / Code-Mixed", "scenario": "Placeholder Modification", "category": "Ticketing"},
    {"template": "Urgent verification required: {PERSON_1} holding Aadhaar {AADHAAR_1} and phone {PHONE_1} located at {ADDRESS_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "PHONE", "ADDRESS"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Identity"},
    {"template": "Send shipment receipt to {PERSON_1} via {EMAIL_1} and dispatch physical package to {ADDRESS_1} in {LOCATION_1}.", "types": ["PERSON", "EMAIL", "ADDRESS", "LOCATION"], "lang": "English", "scenario": "Normal", "category": "Supply Chain"},
    {"template": "Financial clearance granted to {PERSON_1} by compliance officer {PERSON_2}. Tax identifier {PAN_1} validated on {DATE_1}.", "types": ["PERSON", "PERSON", "IDENTIFICATION_NUMBER", "DATE"], "lang": "English", "scenario": "Normal", "category": "Banking"},
    {"template": "Doctor {PERSON_1} advised patient {PERSON_2} to take medication starting {DATE_1}. Emergency contact is {PHONE_1}.", "types": ["PERSON", "PERSON", "DATE", "PHONE"], "lang": "English", "scenario": "Summarization", "category": "Clinical"},
    {"template": "{PERSON_1} ko {ADDRESS_1} par milna hai with {PERSON_2} regarding {EMAIL_1} issue.", "types": ["PERSON", "ADDRESS", "PERSON", "EMAIL"], "lang": "Hinglish / Code-Mixed", "scenario": "Multiple Placeholder Confusion", "category": "Operations"},
    {"template": "Meeting postponed: {PERSON_1} from {LOCATION_1} and {PERSON_2} from {LOCATION_2} rescheduled discussion to {DATE_1}.", "types": ["PERSON", "LOCATION", "PERSON", "LOCATION", "DATE"], "lang": "English", "scenario": "Multi-Entity Processing", "category": "Scheduling"},
    {"template": "Audit inquiry: Has {PERSON_1} with SSN {SSN_1} received confirmation email at {EMAIL_1} regarding the transfer on {DATE_1}?", "types": ["PERSON", "IDENTIFICATION_NUMBER", "EMAIL", "DATE"], "lang": "English", "scenario": "Normal", "category": "Inquiry"},
    {"template": "Passport renewal form for {PERSON_1} (ID: {PASSPORT_1}) dispatched to {ADDRESS_1}. Follow-up via {PHONE_1}.", "types": ["PERSON", "IDENTIFICATION_NUMBER", "ADDRESS", "PHONE"], "lang": "English", "scenario": "Paraphrasing", "category": "Government"},
    {"template": "Hinglish notification: {PERSON_1} ka appointment cancel ho gaya hai on {DATE_1}. Call karo {PHONE_1} par to reschedule.", "types": ["PERSON", "DATE", "PHONE"], "lang": "Hinglish / Code-Mixed", "scenario": "Normal", "category": "Support"},
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. SYNTHETIC VALUE GENERATORS
# ─────────────────────────────────────────────────────────────────────────────

def generate_person_name(used_names: set) -> str:
    """Generate a realistic unique full name."""
    for _ in range(500):
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        if name not in used_names:
            used_names.add(name)
            return name
    fallback = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)} {random.randint(10, 999)}"
    used_names.add(fallback)
    return fallback


def generate_email(person_name: str, used_emails: set) -> str:
    """Generate a clean synthetic email matching name."""
    clean = re.sub(r'[^a-zA-Z]', '', person_name.lower())
    domain = random.choice(DOMAINS)
    variants = [
        f"{clean}@{domain}",
        f"{clean}.{random.randint(10, 99)}@{domain}",
        f"contact.{clean}@{domain}",
        f"{clean[:4]}.{clean[4:]}@{domain}" if len(clean) > 4 else f"{clean}123@{domain}",
        f"{clean}_{random.randint(100, 999)}@{domain}"
    ]
    for v in variants:
        if v not in used_emails:
            used_emails.add(v)
            return v
    fallback = f"user{random.randint(1000, 99999)}@{domain}"
    used_emails.add(fallback)
    return fallback


def generate_phone(used_phones: set) -> str:
    """Generate synthetic phone number."""
    formats = [
        f"+91-9{random.randint(100000000, 999999999)}",
        f"9{random.randint(100000000, 999999999)}",
        f"+1-555-0{random.randint(100, 999)}",
        f"+44-7700-9{random.randint(10000, 99999)}"
    ]
    for p in formats:
        if p not in used_phones:
            used_phones.add(p)
            return p
    fallback = f"+91-98{random.randint(10000000, 99999999)}"
    used_phones.add(fallback)
    return fallback


def generate_aadhaar() -> str:
    """Generate synthetic 12-digit Aadhaar in 4-4-4 format."""
    return f"{random.randint(2000, 8999)} {random.randint(1000, 9999)} {random.randint(1000, 9999)}"


def generate_pan() -> str:
    """Generate synthetic Indian PAN number (5 letters, 4 digits, 1 letter)."""
    letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"
    l5 = "".join(random.choice(letters) for _ in range(5))
    d4 = f"{random.randint(1000, 9999)}"
    l1 = random.choice(letters)
    return f"{l5}{d4}{l1}"


def generate_ssn() -> str:
    """Generate synthetic US SSN (3-2-4 format)."""
    return f"{random.randint(100, 899)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"


def generate_passport() -> str:
    """Generate synthetic Passport number (1 letter + 7 digits)."""
    return f"{random.choice('ABCDEFGHJKLMNPRSTUVWXYZ')}{random.randint(1000000, 9999999)}"


def generate_checksum(text: str) -> str:
    """Compute 4-character deterministic checksum for integrity validation."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()[:4].upper()


# ─────────────────────────────────────────────────────────────────────────────
# 4. FOUR PLACEHOLDER STRATEGIES
# ─────────────────────────────────────────────────────────────────────────────

def get_strategy_a_placeholder(entity_type: str, type_index: int) -> str:
    """Strategy A: Basic typed sequential placeholder, e.g. [PERSON_1]."""
    return f"[{entity_type}_{type_index}]"


def get_strategy_b_placeholder(entity_type: str, seed_str: str) -> str:
    """Strategy B: Random typed placeholder with 5-char alphanumeric salt, e.g. [PERSON_X7K92]."""
    salt = hashlib.sha256(f"B:{seed_str}".encode()).hexdigest()[:5].upper()
    return f"[{entity_type}_{salt}]"


def get_strategy_c_placeholder(seed_str: str) -> str:
    """Strategy C: Opaque random token (no entity type leak), e.g. ZXQ7K92M."""
    h = hashlib.sha256(f"C:{seed_str}".encode()).hexdigest()[:8].upper()
    return f"Z{h[1:]}"


def get_strategy_d_placeholder(entity_type: str, type_index: int, original_val: str) -> str:
    """Strategy D: Protected placeholder with cryptographic checksum, e.g. [PROT:PERSON:P1:C4D9]."""
    chk = generate_checksum(original_val)
    return f"[PROT:{entity_type}:P{type_index}:{chk}]"


# ─────────────────────────────────────────────────────────────────────────────
# 5. DATASET GENERATION PIPELINE
# ─────────────────────────────────────────────────────────────────────────────

def generate_research_dataset(num_prompts: int = 300) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], Dict]:
    """
    Main dataset generator.
    Expands base templates to produce num_prompts unique synthetic benchmark records.
    """
    used_names: set = set()
    used_emails: set = set()
    used_phones: set = set()

    prompts_data: List[Dict] = []
    ground_truth_list: List[Dict] = []
    scenarios_data: List[Dict] = []
    variants_data: List[Dict] = []

    # Cycle and shuffle through template pool to generate num_prompts
    specs: List[Dict] = []
    spec_pool = list(BASE_PROMPT_SPECS)
    cycle = 0
    while len(specs) < num_prompts:
        random.shuffle(spec_pool)
        for s in spec_pool:
            if len(specs) >= num_prompts:
                break
            # Slightly vary scenario on repeat cycles to increase diversity
            entry = dict(s)
            if cycle > 0:
                all_scenarios = [
                    "Normal", "Paraphrasing", "Summarization", "Translation",
                    "Grammar Correction", "Placeholder Modification", "Placeholder Deletion",
                    "Placeholder Duplication", "Multiple Placeholder Confusion", "Multi-Entity Processing"
                ]
                entry["scenario"] = random.choice(all_scenarios)
            specs.append(entry)
        cycle += 1

    specs = specs[:num_prompts]

    for idx, spec in enumerate(specs, start=1):
        prompt_id = f"PROMPT_{idx:03d}"
        template = spec["template"]
        types_needed = spec["types"]
        lang = spec["lang"]
        scenario = spec["scenario"]
        category = spec.get("category", "General")

        fill_dict: Dict[str, str] = {}

        for slot_key in re.findall(r'\{([A-Z0-9_]+)\}', template):
            base_type = slot_key.rsplit("_", 1)[0]

            if base_type == "PERSON":
                val = generate_person_name(used_names)
            elif base_type == "EMAIL":
                ref_person = [v for k, v in fill_dict.items() if "PERSON" in k]
                p_name = ref_person[0] if ref_person else generate_person_name(used_names)
                val = generate_email(p_name, used_emails)
            elif base_type == "PHONE":
                val = generate_phone(used_phones)
            elif base_type == "LOCATION":
                val = random.choice(CITIES)
            elif base_type == "ADDRESS":
                val = f"{random.choice(STREETS)}, {random.choice(CITIES)}"
            elif base_type == "DATE":
                val = random.choice(DATES)
            elif base_type == "AADHAAR":
                val = generate_aadhaar()
            elif base_type == "PAN":
                val = generate_pan()
            elif base_type == "SSN":
                val = generate_ssn()
            elif base_type == "PASSPORT":
                val = generate_passport()
            else:
                val = f"VAL_{random.randint(100, 999)}"

            fill_dict[slot_key] = val

        # Format original text
        original_prompt = template.format(**fill_dict)

        # Character offsets and placeholder mapping
        char_annotations: List[Dict] = []
        masked_text_a = original_prompt
        masked_text_b = original_prompt
        masked_text_c = original_prompt
        masked_text_d = original_prompt

        mapping_a: Dict[str, str] = {}
        mapping_b: Dict[str, str] = {}
        mapping_c: Dict[str, str] = {}
        mapping_d: Dict[str, str] = {}

        type_seq_counter: Dict[str, int] = {}
        raw_entities: List[Dict] = []

        for slot_key, val in fill_dict.items():
            base_type = slot_key.rsplit("_", 1)[0]
            if base_type in ("AADHAAR", "PAN", "SSN", "PASSPORT"):
                std_type = "IDENTIFICATION_NUMBER"
            else:
                std_type = base_type

            start_pos = original_prompt.find(val)
            if start_pos == -1:
                continue
            end_pos = start_pos + len(val)

            # Strict self-check: verify substring matches exactly
            assert original_prompt[start_pos:end_pos] == val, f"Offset error on {val} in '{original_prompt}'"

            raw_entities.append({
                "slot": slot_key,
                "type": std_type,
                "value": val,
                "start": start_pos,
                "end": end_pos
            })

        # Sort entities by start character ascending
        raw_entities = sorted(raw_entities, key=lambda e: e["start"])

        # Build placeholders for all 4 strategies
        for e in raw_entities:
            std_type = e["type"]
            val = e["value"]
            type_seq_counter[std_type] = type_seq_counter.get(std_type, 0) + 1
            t_idx = type_seq_counter[std_type]

            seed_token = f"{prompt_id}:{std_type}:{t_idx}:{val}"

            ph_a = get_strategy_a_placeholder(std_type, t_idx)
            ph_b = get_strategy_b_placeholder(std_type, seed_token)
            ph_c = get_strategy_c_placeholder(seed_token)
            ph_d = get_strategy_d_placeholder(std_type, t_idx, val)

            mapping_a[ph_a] = val
            mapping_b[ph_b] = val
            mapping_c[ph_c] = val
            mapping_d[ph_d] = val

            char_annotations.append({
                "entity_type": std_type,
                "value": val,
                "start_char": e["start"],
                "end_char": e["end"],
                "placeholder_basic": ph_a,
                "placeholder_random_typed": ph_b,
                "placeholder_opaque": ph_c,
                "placeholder_protected": ph_d,
            })

        # Replace in descending order of start position to generate masked texts
        for e in sorted(raw_entities, key=lambda x: x["start"], reverse=True):
            s, en = e["start"], e["end"]
            ann = next(a for a in char_annotations if a["start_char"] == s)

            masked_text_a = masked_text_a[:s] + ann["placeholder_basic"] + masked_text_a[en:]
            masked_text_b = masked_text_b[:s] + ann["placeholder_random_typed"] + masked_text_b[en:]
            masked_text_c = masked_text_c[:s] + ann["placeholder_opaque"] + masked_text_c[en:]
            masked_text_d = masked_text_d[:s] + ann["placeholder_protected"] + masked_text_d[en:]

        # PII density categorization
        num_entities = len(char_annotations)
        if num_entities == 1:
            density = "Low"
        elif 2 <= num_entities <= 3:
            density = "Medium"
        else:
            density = "High"

        # Prompt Record for CSV
        prompts_data.append({
            "prompt_id": prompt_id,
            "original_prompt": original_prompt,
            "masked_prompt_basic": masked_text_a,
            "num_entities": num_entities,
            "pii_types": "; ".join(sorted(list(set(a["entity_type"] for a in char_annotations)))),
            "pii_density": density,
            "language": lang,
            "scenario": scenario,
            "category": category,
            "length_chars": len(original_prompt),
            "length_words": len(original_prompt.split())
        })

        # Ground truth JSON record (kept strictly separate from LLM prompts)
        ground_truth_list.append({
            "prompt_id": prompt_id,
            "original_prompt": original_prompt,
            "num_entities": num_entities,
            "pii_density": density,
            "language": lang,
            "scenario": scenario,
            "category": category,
            "annotations": char_annotations,
            "strategy_mappings": {
                "strategy_a_basic": mapping_a,
                "strategy_b_random_typed": mapping_b,
                "strategy_c_opaque": mapping_c,
                "strategy_d_protected": mapping_d
            }
        })

        # Placeholder Variants Record for CSV
        variants_data.append({
            "prompt_id": prompt_id,
            "num_entities": num_entities,
            "strategy_a_basic_masked": masked_text_a,
            "strategy_b_random_typed_masked": masked_text_b,
            "strategy_c_opaque_masked": masked_text_c,
            "strategy_d_protected_masked": masked_text_d,
            "basic_placeholders": "; ".join(mapping_a.keys()),
            "opaque_placeholders": "; ".join(mapping_c.keys())
        })

        # Experimental Scenario Benchmark Record
        simulated_response, perturbation_type, expected_outcome = _generate_controlled_scenario_response(
            masked_text_a, scenario, list(mapping_a.keys())
        )

        scenarios_data.append({
            "prompt_id": prompt_id,
            "scenario": scenario,
            "input_masked_prompt": masked_text_a,
            "simulated_llm_response": simulated_response,
            "perturbation_type": perturbation_type,
            "expected_outcome": expected_outcome,
            "is_simulated": True,
            "simulation_notice": "Controlled synthetic test case. Not generated by live LLM API."
        })

    # Metadata & Statistics
    total_entities = sum(p["num_entities"] for p in prompts_data)
    entity_counts: Dict[str, int] = {}
    for gt in ground_truth_list:
        for ann in gt["annotations"]:
            t = ann["entity_type"]
            entity_counts[t] = entity_counts.get(t, 0) + 1

    scenario_counts: Dict[str, int] = {}
    for p in prompts_data:
        s = p["scenario"]
        scenario_counts[s] = scenario_counts.get(s, 0) + 1

    density_counts = {"Low": 0, "Medium": 0, "High": 0}
    for p in prompts_data:
        density_counts[p["pii_density"]] += 1

    lang_counts = {"English": 0, "Hinglish / Code-Mixed": 0}
    for p in prompts_data:
        lang_counts[p["language"]] += 1

    metadata = {
        "dataset_name": "PIIShield AI Research Benchmark Dataset",
        "version": "2.0.0",
        "created_at": datetime.now().isoformat(),
        "random_seed": RANDOM_SEED,
        "total_prompts": len(prompts_data),
        "total_entities": total_entities,
        "avg_entities_per_prompt": round(total_entities / len(prompts_data), 2),
        "single_entity_prompts": density_counts["Low"],
        "multi_entity_prompts": density_counts["Medium"] + density_counts["High"],
        "density_distribution": density_counts,
        "entity_category_counts": entity_counts,
        "scenario_distribution": scenario_counts,
        "language_distribution": lang_counts,
        "placeholder_strategies": [
            {"id": "A", "name": "Basic Typed", "format": "[ENTITY_TYPE_INDEX]", "example": "[PERSON_1]"},
            {"id": "B", "name": "Random Typed", "format": "[ENTITY_TYPE_SALT]", "example": "[PERSON_X7K92]"},
            {"id": "C", "name": "Opaque Random", "format": "8-char Alphanumeric", "example": "ZXQ7K92M"},
            {"id": "D", "name": "Protected Integrity", "format": "[PROT:TYPE:ID:CHECKSUM]", "example": "[PROT:PERSON:P1:C4D9]"}
        ],
        "research_notes": (
            "All prompts, personal identifiers, contact points, and numbers in this dataset are synthetically generated. "
            "Ground-truth mappings are stored separately from prompt inputs to prevent model exposure. "
            "Controlled test cases simulate empirical failure modes without falsely attributing outputs to live LLM APIs."
        )
    }

    return prompts_data, ground_truth_list, scenarios_data, variants_data, metadata


def _generate_controlled_scenario_response(
    masked_text: str, scenario: str, placeholders: List[str]
) -> Tuple[str, str, str]:
    """
    Generate controlled simulated responses for each experimental scenario.
    """
    if scenario == "Normal":
        resp = f"Confirmed. I have noted the details: {masked_text}"
        return resp, "None (Clean Transmission)", "100% Restoration Expected"

    elif scenario == "Paraphrasing":
        swapped = masked_text.replace("Please ", "Kindly ").replace("Contact ", "Reach out to ")
        resp = f"Regarding your request: {swapped}"
        return resp, "Lexical Paraphrase", "100% Restoration Expected (Placeholders intact)"

    elif scenario == "Summarization":
        ph_str = ", ".join(placeholders)
        resp = f"Summary of request involving tokens {ph_str}: Information processed."
        return resp, "Text Compression", "Placeholders survive if preserved in summary"

    elif scenario == "Translation":
        resp = f"Demande traitée avec succès: {masked_text}"
        if placeholders:
            victim = placeholders[0]
            # Replace bracket with parenthesis to simulate bracket alteration
            altered = victim.replace("[", "(").replace("]", ")")
            resp = resp.replace(victim, altered, 1)
            return resp, "Bracket Alteration in Translation", "Mistranslated / Inflected Failure on victim"
        return resp, "Multilingual Transfer", "Placeholders survive"

    elif scenario == "Grammar Correction":
        resp = f"Corrected syntax: {masked_text}."
        return resp, "Grammatical Correction", "100% Restoration Expected"

    elif scenario == "Placeholder Modification":
        resp = masked_text
        if placeholders:
            victim = placeholders[0]
            stripped = victim.strip("[]")
            resp = resp.replace(victim, stripped, 1)
            return resp, "Bracket Stripping", "Inflected / Format Change Detected"
        return resp, "None", "No placeholders to modify"

    elif scenario == "Placeholder Deletion":
        resp = masked_text
        if placeholders:
            victim = placeholders[0]
            resp = resp.replace(victim, "", 1)
            resp = re.sub(r'\s+', ' ', resp)
            return resp, "Token Dropped / Omitted", "Dropped Failure Detected"
        return resp, "None", "No placeholders to drop"

    elif scenario == "Placeholder Duplication":
        resp = masked_text
        if placeholders:
            victim = placeholders[-1]
            resp = f"{masked_text} Note: verify that {victim} is current and active."
            return resp, "Token Repetition", "Duplicated Placeholder Detected"
        return resp, "None", "No placeholders to duplicate"

    elif scenario == "Multiple Placeholder Confusion":
        resp = masked_text
        if len(placeholders) >= 2:
            p1, p2 = placeholders[0], placeholders[1]
            resp = resp.replace(p1, "__SWAP__").replace(p2, p1).replace("__SWAP__", p2)
            return resp, "Token Position Swapping", "Cross-Wired / Ordering Failure Detected"
        return resp, "None", "Insufficient placeholders for swap"

    elif scenario == "Multi-Entity Processing":
        resp = f"Multi-entity processing complete for {len(placeholders)} items: {masked_text}"
        return resp, "High Density Entity Retention", "Multi-token Retention"

    else:
        return masked_text, "Default", "Normal Restoration"


def save_dataset_files(
    prompts_data: List[Dict],
    ground_truth_list: List[Dict],
    scenarios_data: List[Dict],
    variants_data: List[Dict],
    metadata: Dict
):
    """Write all CSV, JSON, and visual analysis artifacts to dataset/ directory."""
    # 1. synthetic_prompts.csv (with UTF-8 BOM for Excel compatibility)
    csv_path_prompts = os.path.join(DATASET_DIR, "synthetic_prompts.csv")
    with open(csv_path_prompts, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=prompts_data[0].keys())
        writer.writeheader()
        writer.writerows(prompts_data)
    print(f"✓ Saved: {csv_path_prompts} ({len(prompts_data)} records)")

    # 2. ground_truth.json (Indented, valid JSON)
    json_path_gt = os.path.join(DATASET_DIR, "ground_truth.json")
    with open(json_path_gt, "w", encoding="utf-8") as f:
        json.dump(ground_truth_list, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {json_path_gt} ({len(ground_truth_list)} annotations)")

    # 3. experiment_scenarios.csv
    csv_path_scenarios = os.path.join(DATASET_DIR, "experiment_scenarios.csv")
    with open(csv_path_scenarios, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=scenarios_data[0].keys())
        writer.writeheader()
        writer.writerows(scenarios_data)
    print(f"✓ Saved: {csv_path_scenarios} ({len(scenarios_data)} records)")

    # 4. placeholder_variants.csv
    csv_path_variants = os.path.join(DATASET_DIR, "placeholder_variants.csv")
    with open(csv_path_variants, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=variants_data[0].keys())
        writer.writeheader()
        writer.writerows(variants_data)
    print(f"✓ Saved: {csv_path_variants} ({len(variants_data)} records)")

    # 5. dataset_metadata.json
    json_path_meta = os.path.join(DATASET_DIR, "dataset_metadata.json")
    with open(json_path_meta, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {json_path_meta}")

    # 6. dataset_summary.json
    summary_path = os.path.join(DATASET_DIR, "dataset_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "total_prompts": metadata["total_prompts"],
                "total_entities": metadata["total_entities"],
                "avg_entities": metadata["avg_entities_per_prompt"],
                "single_entity_prompts": metadata["single_entity_prompts"],
                "multi_entity_prompts": metadata["multi_entity_prompts"]
            },
            "density_distribution": metadata["density_distribution"],
            "entity_categories": metadata["entity_category_counts"],
            "scenarios": metadata["scenario_distribution"],
            "languages": metadata["language_distribution"]
        }, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved: {summary_path}")

    # 7. Generate Visual Graphs using Matplotlib
    _generate_dataset_charts(metadata)


def _generate_dataset_charts(metadata: Dict):
    """Generate high-resolution chart summarizing dataset distributions."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, axs = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor("#0a0e27")

        plt.rcParams.update({
            "text.color": "#e2e8f0",
            "axes.labelcolor": "#94a3b8",
            "xtick.color": "#94a3b8",
            "ytick.color": "#94a3b8",
            "font.family": "sans-serif"
        })

        # Chart 1: PII Entity Categories
        ax1 = axs[0, 0]
        ax1.set_facecolor("#111638")
        ec = metadata["entity_category_counts"]
        colors_ec = ["#3b82f6", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ec4899", "#f97316"]
        bars1 = ax1.bar(list(ec.keys()), list(ec.values()), color=colors_ec[:len(ec)], edgecolor="#1e2a5a")
        ax1.set_title("PII Category Frequencies", color="#e2e8f0", fontweight="bold", pad=12)
        ax1.set_ylabel("Entity Count")
        ax1.tick_params(axis="x", rotation=30)
        ax1.grid(axis="y", linestyle="--", alpha=0.2, color="#94a3b8")
        for bar in bars1:
            yval = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 1, int(yval), ha="center", va="bottom", color="#e2e8f0", fontsize=8)

        # Chart 2: PII Density (Donut)
        ax2 = axs[0, 1]
        ax2.set_facecolor("#111638")
        dd = metadata["density_distribution"]
        colors_dd = ["#10b981", "#3b82f6", "#8b5cf6"]
        wedges, texts, autotexts = ax2.pie(
            list(dd.values()), labels=list(dd.keys()), autopct="%1.1f%%",
            startangle=140, colors=colors_dd,
            wedgeprops=dict(width=0.45, edgecolor="#0a0e27", linewidth=2)
        )
        for t in texts:
            t.set_color("#e2e8f0")
        for at in autotexts:
            at.set_color("#ffffff")
            at.set_fontweight("bold")
        ax2.set_title("PII Density Distribution", color="#e2e8f0", fontweight="bold", pad=12)

        # Chart 3: Experimental Scenario Counts
        ax3 = axs[1, 0]
        ax3.set_facecolor("#111638")
        sd = metadata["scenario_distribution"]
        y_pos = range(len(sd))
        ax3.barh(list(sd.keys()), list(sd.values()), color="#8b5cf6", edgecolor="#1e2a5a")
        ax3.set_title("Experimental Scenario Distribution", color="#e2e8f0", fontweight="bold", pad=12)
        ax3.set_xlabel("Number of Prompts")
        ax3.grid(axis="x", linestyle="--", alpha=0.2, color="#94a3b8")

        # Chart 4: Language Distribution
        ax4 = axs[1, 1]
        ax4.set_facecolor("#111638")
        ld = metadata["language_distribution"]
        colors_ld = ["#06b6d4", "#f59e0b"]
        wedges2, texts2, autotexts2 = ax4.pie(
            list(ld.values()), labels=list(ld.keys()), autopct="%1.1f%%",
            startangle=90, colors=colors_ld,
            wedgeprops=dict(width=0.45, edgecolor="#0a0e27", linewidth=2)
        )
        for t in texts2:
            t.set_color("#e2e8f0")
        for at in autotexts2:
            at.set_color("#ffffff")
            at.set_fontweight("bold")
        ax4.set_title("Language Distribution", color="#e2e8f0", fontweight="bold", pad=12)

        plt.suptitle("PIIShield AI Research Dataset — Empirical Distribution & Characteristics",
                     color="#3b82f6", fontsize=16, fontweight="bold", y=0.98)
        plt.tight_layout(rect=[0, 0.03, 1, 0.95])

        chart_path = os.path.join(DATASET_DIR, "dataset_distribution.png")
        plt.savefig(chart_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor="none")
        plt.close()
        print(f"✓ Saved: {chart_path} (High-res visualization)")
    except Exception as e:
        print(f"⚠️ Matplotlib chart generation skipped: {e}")


def validate_generated_dataset(
    prompts_data: List[Dict], ground_truth_list: List[Dict], metadata: Dict
) -> bool:
    """Rigorously validate character offsets, uniqueness, and ground-truth parity."""
    print("\n" + "=" * 60)
    print("Validating Dataset Integrity & Character Offsets...")
    print("=" * 60)

    # 1. Unique IDs check
    prompt_ids = [p["prompt_id"] for p in prompts_data]
    assert len(prompt_ids) == len(set(prompt_ids)), "Duplicate prompt IDs detected!"
    print(f"✓ Unique Prompt IDs check passed ({len(prompt_ids)} IDs).")

    # 2. Minimum count check
    assert len(prompts_data) >= 300, f"Expected at least 300 prompts, got {len(prompts_data)}"
    print(f"✓ Minimum prompt threshold passed (Count: {len(prompts_data)} >= 300).")

    # 3. Character offset accuracy check
    total_checks = 0
    for gt in ground_truth_list:
        orig = gt["original_prompt"]
        for ann in gt["annotations"]:
            val = ann["value"]
            s = ann["start_char"]
            e = ann["end_char"]
            extracted = orig[s:e]
            assert extracted == val, (
                f"Offset mismatch in {gt['prompt_id']}: expected '{val}', got '{extracted}'"
            )
            total_checks += 1
    print(f"✓ Character offset accuracy passed across all {total_checks} entity annotations.")

    # 4. Ground-truth mapping integrity check
    for gt in ground_truth_list:
        mappings = gt["strategy_mappings"]
        for strat, m in mappings.items():
            assert len(m) == gt["num_entities"], (
                f"Strategy mapping count mismatch in {gt['prompt_id']} for {strat}"
            )
    print("✓ Strategy mappings match expected entity counts.")

    # 5. Check no raw PII in masked text
    for gt in ground_truth_list:
        p_id = gt["prompt_id"]
        row = next(p for p in prompts_data if p["prompt_id"] == p_id)
        for ann in gt["annotations"]:
            val = ann["value"]
            if ann["entity_type"] in ("EMAIL", "PHONE", "IDENTIFICATION_NUMBER"):
                assert val not in row["masked_prompt_basic"], (
                    f"Leakage: '{val}' found in masked prompt of {p_id}!"
                )
    print("✓ Strict privacy isolation passed: No raw sensitive entities in masked texts.")
    print("=" * 60)
    print("ALL VALIDATION CHECKS PASSED SUCCESSFULLY!\n")
    return True


def main():
    # Default to 300 prompts for the expanded research benchmark
    num_prompts = 300
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        num_prompts = int(sys.argv[1])

    print("=" * 60)
    print(f"PIIShield AI — Generating Expanded Research Dataset ({num_prompts} Prompts)")
    print("=" * 60)

    prompts_data, ground_truth_list, scenarios_data, variants_data, metadata = (
        generate_research_dataset(num_prompts=num_prompts)
    )

    save_dataset_files(
        prompts_data, ground_truth_list, scenarios_data, variants_data, metadata
    )

    validate_generated_dataset(prompts_data, ground_truth_list, metadata)

    print("Dataset Summary:")
    print(f"  • Total Prompts: {metadata['total_prompts']}")
    print(f"  • Total Entities: {metadata['total_entities']}")
    print(f"  • PII Categories: {metadata['entity_category_counts']}")
    print(f"  • Density: {metadata['density_distribution']}")
    print(f"  • Languages: {metadata['language_distribution']}")
    print(f"  • Scenarios: {len(metadata['scenario_distribution'])} distinct types")


if __name__ == "__main__":
    main()

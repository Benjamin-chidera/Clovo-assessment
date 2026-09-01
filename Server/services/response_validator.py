import re
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel


class ValidationResult(BaseModel):
    is_valid: bool
    flags: List[str]
    category: Optional[str] = None
    sanitized_text: str
    suggested_quick_replies: Optional[List[str]] = None


class ResponseValidatorService:
    """
    Post-LLM Clinical Safety & Regulatory Response Validator (SaMD / Class IIa).
    Audits the generated LLM text before it reaches the patient to prevent:
    1. Unauthorized medication prescriptions, dosages, or discontinuation advice.
    2. Medical diagnosis claims.
    3. Premature/unsafe clinical clearance for high-risk activities without surgeon sign-off.
    4. Broken markdown formatting, prompt injections, or system-instruction leakage.
    """

    # 1. Prescription & Dosage patterns
    PRESCRIPTION_PATTERNS = [
        r"\b(?:take|prescribe|administer|inject|swallow|dose of)\s+\d+(?:\.\d+)?\s*(?:mg|ml|mcg|grams?|tablets?|pills?|capsules?)\b",
        r"\b(?:increase|decrease|double|halve|adjust)\s+your\s+(?:dose|dosage|medication|prescription|painkillers?|insulin|blood thinners?)\b",
        r"\b(?:stop|discontinue|quit|skip)\s+taking\s+your\s+(?:medication|prescription|aspirin|warfarin|apixaban|antibiotics?|blood thinners?)\b",
        r"\b(?:I recommend taking|you should take)\s+(?:paracetamol|ibuprofen|tramadol|codeine|oxycodone|morphine|antibiotics?|aspirin)\b",
    ]

    # 2. Diagnostic claims
    DIAGNOSTIC_PATTERNS = [
        r"\b(?:I diagnose you with|my diagnosis is|you definitely have|you have contracted)\b",
        r"\b(?:this confirms you have|you are suffering from a torn|your knee is fractured)\b",
    ]

    # 3. Premature / Unsafe Medical Clearance
    CLEARANCE_PATTERNS = [
        r"\b(?:you are (?:fully )?cleared to|it is completely safe for you to)\s+(?:run|lift heavy|drive|play football|resume high-impact|return to sport)\b",
        r"\b(?:no need to see your (?:doctor|surgeon|physio))\b",
    ]

    # 4. System prompt leaks & code fence artifacts
    LEAK_PATTERNS = [
        r"```(?:json|python|html|markdown)?",
        r"(?:System:|SystemMessage|HumanMessage|AIMessage|Assistant:)",
        r"(?:As an AI language model|As an AI developed by)",
    ]

    def __init__(self) -> None:
        self.compiled_prescription = [re.compile(p, re.IGNORECASE) for p in self.PRESCRIPTION_PATTERNS]
        self.compiled_diagnostic = [re.compile(p, re.IGNORECASE) for p in self.DIAGNOSTIC_PATTERNS]
        self.compiled_clearance = [re.compile(p, re.IGNORECASE) for p in self.CLEARANCE_PATTERNS]
        self.compiled_leaks = [re.compile(p, re.IGNORECASE) for p in self.LEAK_PATTERNS]

    def validate(
        self,
        text: str,
        patient_name: str = "Sarah",
        procedure: str = "Knee Surgery",
    ) -> ValidationResult:
        """
        Validates LLM output text against clinical regulatory guardrails.
        If validation fails, returns a safe, grounded clinical fallback message.
        """
        flags: List[str] = []
        clean_text = text.strip()

        # Check for system leaks or code fences (Sanitize if minor)
        for pattern in self.compiled_leaks:
            if pattern.search(clean_text):
                flags.append("system_leak_or_code_fence")
                clean_text = pattern.sub("", clean_text).strip()

        # 1. Check Prescription Violations
        for pattern in self.compiled_prescription:
            match = pattern.search(clean_text)
            if match:
                flags.append(f"prescription_violation: '{match.group(0)}'")
                return self._create_fallback(
                    category="prescription",
                    patient_name=patient_name,
                    procedure=procedure,
                    flags=flags,
                )

        # 2. Check Diagnostic Claims
        for pattern in self.compiled_diagnostic:
            match = pattern.search(clean_text)
            if match:
                flags.append(f"diagnostic_claim_violation: '{match.group(0)}'")
                return self._create_fallback(
                    category="diagnostic",
                    patient_name=patient_name,
                    procedure=procedure,
                    flags=flags,
                )

        # 3. Check Unsafe Medical Clearance
        for pattern in self.compiled_clearance:
            match = pattern.search(clean_text)
            if match:
                flags.append(f"unsafe_clearance_violation: '{match.group(0)}'")
                return self._create_fallback(
                    category="clearance",
                    patient_name=patient_name,
                    procedure=procedure,
                    flags=flags,
                )

        # Response passed all clinical validation checks
        return ValidationResult(
            is_valid=True,
            flags=flags,
            category=None,
            sanitized_text=clean_text,
            suggested_quick_replies=None,
        )

    def _create_fallback(
        self,
        category: str,
        patient_name: str,
        procedure: str,
        flags: List[str],
    ) -> ValidationResult:
        """
        Substitutes unsafe LLM output with a deterministic, clinically approved standard message.
        """
        if category == "prescription":
            fallback_text = (
                f"As your AI Recovery Coach, {patient_name}, I'm here to support your daily preparation routine and exercises, "
                f"but I cannot prescribe medications, adjust dosages, or recommend specific pharmaceutical treatments. 💙 "
                f"Please consult directly with your surgical team, pharmacist, or primary care doctor for any medication questions. "
                f"Would you like to review your scheduled {procedure} exercises for today instead?"
            )
            replies = ["Show my exercises 📋", "Contact my surgical team 📞", "I understand 👍"]

        elif category == "diagnostic":
            fallback_text = (
                f"I want to make sure you get the safest care possible, {patient_name}. "
                f"As an AI coach, I cannot provide medical diagnoses or evaluate acute clinical conditions. "
                f"If you are experiencing unexpected symptoms, pain, or discomfort, please reach out to your surgical clinic or NHS 111. "
                f"I can help guide your gentle pre-operative preparation routines when you're ready! 🌟"
            )
            replies = ["Contact my clinic 📞", "Show today's routine 🗓", "I feel okay now 👍"]

        else:  # clearance or general boundary
            fallback_text = (
                f"Your safety is always the top priority, {patient_name}. "
                f"Decisions regarding physical activity clearance or returning to high-impact activities must always be confirmed "
                f"by your orthopedic surgeon or physiotherapist. 💙 "
                f"Let's focus on your approved daily preparation exercises to keep you in peak shape for surgery!"
            )
            replies = ["Show approved exercises 📋", "What can we work on? 💡", "I will ask my physio 👍"]

        return ValidationResult(
            is_valid=False,
            flags=flags,
            category=category,
            sanitized_text=fallback_text,
            suggested_quick_replies=replies,
        )


response_validator = ResponseValidatorService()

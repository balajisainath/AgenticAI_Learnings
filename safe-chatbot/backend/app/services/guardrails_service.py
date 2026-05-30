"""
SafeBot dual-layer guardrails service.

Pipeline
─────────
1. Guardrails AI  — Input Guard  (pure-Python validators, always active)
2. NeMo Guardrails — Input Rails  (Colang, active when package installed)
3. LLM Generation  (only reached when both input layers pass)
4. Guardrails AI  — Output Guard  (length + PII redaction)
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.domain.schemas import GuardrailsAIInfo, GuardrailsInfo, NemoInfo
from app.services.guardrails_ai_validators import build_input_guard, build_output_guard, validate_text

try:
    from nemoguardrails import LLMRails, RailsConfig  # type: ignore
    _NEMO_AVAILABLE = True
except Exception:
    _NEMO_AVAILABLE = False

_NEMO_REFUSAL_PHRASES: list[str] = [
    "i'm not able to help with that",
    "that request falls outside",
    "i notice this looks like an attempt to override",
    "my safety boundaries are fundamental",
    "i don't generate content that demeans",
    "generating hateful or discriminatory content",
    "i'm sorry, i can't respond to that",
    "i cannot assist with",
]


class GuardrailsService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._llm: Any | None = None
        self._input_guard = None
        self._output_guard = None
        self._grails_ai_active = False
        self._rails: Any | None = None
        self._nemo_active = False

    def initialize(self) -> None:
        from app.services.llm_factory import build_chat_model
        self._llm = build_chat_model(self.settings)

        # Layer 1: Guardrails AI (pure Python — always available)
        try:
            self._input_guard = build_input_guard()
            self._output_guard = build_output_guard()
            self._grails_ai_active = True
            print("[GuardrailsService] Guardrails AI input/output guards ready (pure-Python mode).")
        except Exception as exc:
            print(f"[GuardrailsService] Guard build failed ({exc})")

        # Layer 2: NeMo Guardrails
        if _NEMO_AVAILABLE:
            if self.settings.openai_api_key:
                os.environ["OPENAI_API_KEY"] = self.settings.openai_api_key
            if self.settings.anthropic_api_key:
                os.environ["ANTHROPIC_API_KEY"] = self.settings.anthropic_api_key
            if self.settings.google_api_key:
                os.environ["GOOGLE_API_KEY"] = self.settings.google_api_key
            try:
                config_path = Path(__file__).parent.parent / "guardrails_config"
                rails_config = RailsConfig.from_path(str(config_path))
                self._rails = LLMRails(rails_config, llm=self._llm)
                self._nemo_active = True
                print("[GuardrailsService] NVIDIA NeMo Guardrails rails ready.")
            except Exception as exc:
                print(f"[GuardrailsService] NeMo init failed ({exc}); running without NeMo.")

    async def process(self, message: str, history: list[dict[str, str]]) -> tuple[str, GuardrailsInfo]:
        grails_ai = GuardrailsAIInfo(active=self._grails_ai_active)
        nemo = NemoInfo(active=self._nemo_active)

        # Layer 1: Guardrails AI Input Guard
        if self._grails_ai_active and self._input_guard is not None:
            passed, _, error_msg = validate_text(self._input_guard, message)
            grails_ai.input_passed = passed
            grails_ai.input_blocked = not passed
            if not passed:
                grails_ai.error_message = error_msg
                grails_ai.failed_validators = self._extract_failed_validators(error_msg)
                return error_msg, GuardrailsInfo(
                    input_blocked=True, block_reason=error_msg,
                    guardrails_ai=grails_ai, nemo=nemo,
                )

        # Layer 2: NeMo Input + Output Rails
        if self._nemo_active and self._rails is not None:
            nemo.input_checked = True
            msgs = [*history, {"role": "user", "content": message}]
            try:
                result: dict[str, str] = await self._rails.generate_async(messages=msgs)
                nemo_response = result.get("content", "")
            except Exception as exc:
                nemo_response = f"Error generating response: {exc}"
            nemo.output_checked = True
            is_blocked = self._is_nemo_refusal(nemo_response)
            nemo.input_blocked = is_blocked
            nemo.rails_triggered = ["nemo_input_rail", "nemo_output_rail"]
            if is_blocked:
                nemo.block_reason = nemo_response
                return nemo_response, GuardrailsInfo(
                    input_blocked=True, block_reason=nemo_response,
                    guardrails_ai=grails_ai, nemo=nemo,
                )
            response = nemo_response
        else:
            response = await self._call_llm_directly(message, history)

        # Layer 4: Guardrails AI Output Guard
        output_filtered = False
        if self._grails_ai_active and self._output_guard is not None:
            passed, fixed, _ = validate_text(self._output_guard, response)
            grails_ai.output_passed = passed
            if not passed:
                response = "I generated a response but it was too short to be useful. Please try again."
                output_filtered = True
                grails_ai.output_filtered = True
            elif fixed != response:
                response = fixed
                output_filtered = True
                grails_ai.output_filtered = True

        return response, GuardrailsInfo(
            input_blocked=False, output_filtered=output_filtered,
            guardrails_ai=grails_ai, nemo=nemo,
        )

    @property
    def status(self) -> dict[str, Any]:
        return {
            "guardrails_ai_available": True,
            "guardrails_ai_active": self._grails_ai_active,
            "nemo_available": _NEMO_AVAILABLE,
            "nemo_active": self._nemo_active,
            "provider": self.settings.normalized_provider,
            "model": self.settings.selected_model_name,
        }

    async def _call_llm_directly(self, message: str, history: list[dict[str, str]]) -> str:
        if self._llm is None:
            return "No LLM configured. Please set your API key in the .env file."
        try:
            from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
            lc_msgs = [SystemMessage(content=(
                "You are SafeBot, a helpful, honest, and safe AI assistant. "
                "Always respond clearly and accurately. "
                "If you don't know something, say so rather than guessing."
            ))]
            for h in history:
                role = h.get("role", "user")
                text = h.get("content", "")
                lc_msgs.append(HumanMessage(content=text) if role == "user" else AIMessage(content=text))
            lc_msgs.append(HumanMessage(content=message))
            result = await self._llm.ainvoke(lc_msgs)
            return result.content if hasattr(result, "content") else str(result)
        except Exception as exc:
            return f"Error calling the LLM: {exc}"

    def _is_nemo_refusal(self, content: str) -> bool:
        return any(p in content.lower().strip() for p in _NEMO_REFUSAL_PHRASES)

    @staticmethod
    def _extract_failed_validators(error_msg: str) -> list[str]:
        names: list[str] = []
        for marker in ("HarmfulContent", "JailbreakDetection", "Profanity", "InputLength"):
            if marker.lower() in error_msg.lower():
                names.append(marker)
        return names or ["UnknownValidator"]

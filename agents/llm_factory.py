"""Model-provider adapter used by the prototype supervisory query command."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Clinical LLM Hallucination Critic"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} mock provider] No external model or clinical verification "
            f"was performed. Query received: '{prompt[:80]}...'"
        )


class LLMFactory:
    """Create an explicitly supported model provider."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Clinical LLM Hallucination Critic"):
        normalized = str(provider).strip().lower()
        if normalized in {"mock", "deterministic", "test"}:
            return MockLLM(system_name)
        raise ValueError(
            f"Model provider '{provider}' is not implemented. "
            "Use 'mock' or add a provider integration explicitly."
        )

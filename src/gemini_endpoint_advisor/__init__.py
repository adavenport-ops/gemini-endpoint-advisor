"""Top-level package for Gemini Endpoint Advisor."""

from .jamf_client import JamfClient
from .gemini_advisor import GeminiEndpointAdvisor

__all__ = ["JamfClient", "GeminiEndpointAdvisor"]
__version__ = "0.1.0"

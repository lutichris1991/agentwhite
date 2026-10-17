import unittest
from unittest.mock import patch

from agentwhite.local_ai import analyze_findings


class LocalAIAnalystTests(unittest.TestCase):
    def test_rule_fallback_works_without_ollama(self):
        findings = [
            {
                "device_id": "lan-test",
                "category": "service-exposure",
                "severity": "high",
                "title": "RTSP service verified on TCP/554",
                "proof": {"address": "192.168.1.20", "port": 554},
                "remediation": "Require authentication and restrict camera access.",
                "status": "verified",
            }
        ]
        with patch("agentwhite.local_ai.available_models", return_value=[]):
            result = analyze_findings(findings)
        self.assertEqual(result["engine"], "AgentWhite offline rule analyst")
        self.assertIn("1 recorded findings", result["summary"])
        self.assertEqual(result["priorities"][0]["severity"], "high")

    def test_requested_unavailable_model_falls_back_safely(self):
        with patch("agentwhite.local_ai.available_models", return_value=[]):
            result = analyze_findings([], model="not-installed")
        self.assertIsNone(result["model"])
        self.assertEqual(result["analysis"], "")


if __name__ == "__main__":
    unittest.main()

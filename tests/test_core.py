import tempfile
import unittest
from pathlib import Path

from agentwhite.analysis import analyze_wifi
from agentwhite.storage import StateStore


class AnalysisTests(unittest.TestCase):
    def test_wep_is_critical(self):
        device = {
            "name": "Lab-WEP",
            "address": "00:11:22:33:44:55",
            "details": {"authentication": "WEP", "encryption": "WEP"},
        }
        findings = analyze_wifi(device)
        self.assertEqual(findings[0]["severity"], "critical")

    def test_wpa3_is_informational(self):
        device = {
            "name": "Lab-WPA3",
            "address": "00:11:22:33:44:56",
            "details": {"authentication": "WPA3-Personal", "encryption": "CCMP"},
        }
        findings = analyze_wifi(device)
        self.assertEqual(findings[0]["severity"], "info")


class StorageTests(unittest.TestCase):
    def test_enrollment_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            store.upsert_devices([
                {
                    "id": "lan-test",
                    "kind": "lan",
                    "name": "192.168.1.20",
                    "address": "192.168.1.20",
                    "details": {"mac": "00:11:22:33:44:55"},
                }
            ])
            updated = store.set_enrolled("lan-test", True)
            self.assertTrue(updated["enrolled"])
            self.assertTrue(store.get_device("lan-test")["enrolled"])

    def test_finding_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            store.upsert_devices([
                {
                    "id": "lan-test",
                    "kind": "lan",
                    "name": "192.168.1.20",
                    "address": "192.168.1.20",
                    "details": {},
                }
            ])
            store.add_finding(
                device_id="lan-test",
                category="service-exposure",
                severity="info",
                title="HTTP verified",
                proof={"port": 80},
                remediation="Restrict access.",
            )
            finding = store.list_findings("lan-test")[0]
            self.assertEqual(finding["proof"]["port"], 80)


if __name__ == "__main__":
    unittest.main()

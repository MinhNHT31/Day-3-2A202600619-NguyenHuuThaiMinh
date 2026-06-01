"""
Test Suite: Intermarket Analysis Agent
Tests the 5 tools and basic agent functionality.

Run:
    python -m pytest tests/ -v
    python tests/test_agent_scenario.py
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.market_data import get_market_data
from src.tools.correlation_analysis import calculate_correlation
from src.tools.anomaly_detection import detect_anomalies
from src.tools.risk_management import calculate_risk_scenario
from src.tools.reporting import generate_report


class TestMarketDataTool(unittest.TestCase):
    """Test Tool 1: Multi-Asset Data API"""

    def test_valid_assets(self):
        for asset in ["DXY", "GOLD", "OIL_BRENT", "OIL_WTI", "BTC"]:
            result = json.loads(get_market_data(asset=asset, period="1d"))
            self.assertNotIn("error", result, f"Error fetching {asset}")
            self.assertIn("current_price", result)
            self.assertIn("trend", result)
            self.assertIn(result["trend"], ["BULLISH", "BEARISH", "NEUTRAL"])
            print(f"  ✅ {asset}: ${result['current_price']} ({result['trend']})")

    def test_invalid_asset_returns_error(self):
        result = json.loads(get_market_data(asset="INVALID"))
        self.assertIn("error", result)
        print(f"  ✅ Invalid asset correctly returns error: {result['error'][:50]}")

    def test_all_periods(self):
        for period in ["1h", "1d", "1w"]:
            result = json.loads(get_market_data(asset="GOLD", period=period))
            self.assertNotIn("error", result)
            print(f"  ✅ GOLD period={period}: ${result['current_price']}")


class TestCorrelationTool(unittest.TestCase):
    """Test Tool 2: Correlation Analysis"""

    def test_returns_three_pairs(self):
        result = json.loads(calculate_correlation(timeframe="1d"))
        self.assertIn("correlations", result)
        pairs = result["correlations"]
        self.assertIn("DXY_vs_GOLD", pairs)
        self.assertIn("DXY_vs_OIL", pairs)
        self.assertIn("GOLD_vs_OIL", pairs)
        print(f"  ✅ Correlations: {[(k, v['coefficient']) for k, v in pairs.items()]}")

    def test_correlation_range(self):
        result = json.loads(calculate_correlation(timeframe="1d"))
        for pair, data in result["correlations"].items():
            coef = data["coefficient"]
            self.assertGreaterEqual(coef, -1.0, f"{pair} correlation < -1")
            self.assertLessEqual(coef, 1.0, f"{pair} correlation > 1")

    def test_market_regime_present(self):
        result = json.loads(calculate_correlation(timeframe="1w"))
        self.assertIn("market_regime", result)
        print(f"  ✅ Market regime: {result['market_regime']}")


class TestAnomalyDetectionTool(unittest.TestCase):
    """Test Tool 3: Anomaly Detection Engine"""

    def test_returns_market_status(self):
        result = json.loads(detect_anomalies(threshold=0.5))
        self.assertIn("market_status", result)
        self.assertIn(result["market_status"], ["NORMAL", "WATCH", "ANOMALOUS", "CRITICAL"])
        print(f"  ✅ Market status: {result['market_status']}, anomalies: {result['anomalies_detected']}")

    def test_anomaly_structure(self):
        result = json.loads(detect_anomalies(threshold=0.1))  # Low threshold = more anomalies
        for anomaly in result.get("anomalies", []):
            self.assertIn("name", anomaly)
            self.assertIn("severity", anomaly)
            self.assertIn("explanation", anomaly)
            self.assertIn("suggested_action", anomaly)

    def test_low_threshold_catches_more(self):
        result_strict = json.loads(detect_anomalies(threshold=0.9))
        result_lenient = json.loads(detect_anomalies(threshold=0.1))
        # Lower threshold should detect same or more anomalies
        self.assertGreaterEqual(
            result_lenient["anomalies_detected"],
            result_strict["anomalies_detected"]
        )
        print(f"  ✅ Threshold 0.9: {result_strict['anomalies_detected']} | Threshold 0.1: {result_lenient['anomalies_detected']}")


class TestRiskManagementTool(unittest.TestCase):
    """Test Tool 4: Risk Management Tool"""

    def test_high_oil_increases_cpi(self):
        baseline = json.loads(calculate_risk_scenario(oil_price=80.0, scenario="high"))
        high_oil  = json.loads(calculate_risk_scenario(oil_price=110.0, scenario="high"))
        self.assertGreater(
            high_oil["macro_projections"]["projected_cpi"],
            baseline["macro_projections"]["projected_cpi"],
        )
        print(f"  ✅ Oil $80 → CPI {baseline['macro_projections']['projected_cpi']}% | "
              f"Oil $110 → CPI {high_oil['macro_projections']['projected_cpi']}%")

    def test_high_oil_higher_risk(self):
        low_risk  = json.loads(calculate_risk_scenario(oil_price=60.0, scenario="low"))
        high_risk = json.loads(calculate_risk_scenario(oil_price=120.0, scenario="high"))
        risk_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        self.assertGreater(
            risk_order[high_risk["risk_level"]],
            risk_order[low_risk["risk_level"]],
        )
        print(f"  ✅ Oil $60 (low) → {low_risk['risk_level']} | Oil $120 (high) → {high_risk['risk_level']}")

    def test_invalid_scenario(self):
        result = json.loads(calculate_risk_scenario(oil_price=80.0, scenario="extreme"))
        self.assertIn("error", result)

    def test_recommendations_present(self):
        result = json.loads(calculate_risk_scenario(oil_price=95.0, scenario="high"))
        self.assertIn("recommendations", result)
        self.assertGreater(len(result["recommendations"]), 0)


class TestReportingTool(unittest.TestCase):
    """Test Tool 5: Reporting Tool"""

    def test_generates_file(self):
        import os
        sample_data = json.dumps({
            "prices": {
                "GOLD": {"current_price": 2348.5, "trend": "BULLISH"},
                "DXY":  {"current_price": 104.35, "trend": "BEARISH"},
            },
            "correlations": {"market_regime": "CLASSIC_MACRO"},
        })
        result = json.loads(generate_report(analysis_data=sample_data))
        self.assertEqual(result["status"], "SUCCESS")
        self.assertTrue(os.path.exists(result["report_path"]))
        print(f"  ✅ Report generated: {result['report_name']}")

    def test_handles_empty_data(self):
        result = json.loads(generate_report(analysis_data="{}"))
        self.assertEqual(result["status"], "SUCCESS")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🧪 INTERMARKET ANALYSIS AGENT — TEST SUITE")
    print("="*60 + "\n")

    loader  = unittest.TestLoader()
    suite   = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestMarketDataTool))
    suite.addTests(loader.loadTestsFromTestCase(TestCorrelationTool))
    suite.addTests(loader.loadTestsFromTestCase(TestAnomalyDetectionTool))
    suite.addTests(loader.loadTestsFromTestCase(TestRiskManagementTool))
    suite.addTests(loader.loadTestsFromTestCase(TestReportingTool))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    print("\n" + "="*60)
    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    print(f"  Results: {passed}/{total} tests passed")
    print("="*60)

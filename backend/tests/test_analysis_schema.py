import unittest

from backend.services.analysis_schema import AnalysisMetric, RealEstateAnalysisResult


class AnalysisSchemaTests(unittest.TestCase):
    def test_analysis_result_keeps_structured_defaults(self):
        result = RealEstateAnalysisResult(executive_summary="Clear summary.")

        self.assertEqual(result.executive_summary, "Clear summary.")
        self.assertEqual(result.metrics, [])
        self.assertEqual(result.missing_data, [])
        self.assertEqual(result.excel_fields, [])

    def test_metric_accepts_numeric_value_and_source(self):
        metric = AnalysisMetric(
            key="gross_yield",
            label="Gross yield",
            value=4.25,
            unit="%",
            source="rent-roll.pdf",
        )

        self.assertEqual(metric.value, 4.25)
        self.assertEqual(metric.unit, "%")
        self.assertEqual(metric.source, "rent-roll.pdf")


if __name__ == "__main__":
    unittest.main()

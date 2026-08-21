import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "estimate_databento_cost.py"
SPEC = importlib.util.spec_from_file_location("estimate_databento_cost", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class FakeMetadata:
    def __init__(self):
        self.calls = []

    def get_cost(self, **request):
        self.calls.append(request)
        return 1.2345678


class FakeClient:
    def __init__(self):
        self.metadata = FakeMetadata()


class DatabentoCostTests(unittest.TestCase):
    def test_builds_bounded_opra_request(self):
        request = MODULE.build_request(
            start="2026-08-03T09:30:00-04:00",
            end="2026-08-03T16:00:00-04:00",
            schema="cbbo-1s",
            symbols=["SPY.OPT"],
            stype_in="parent",
        )
        self.assertEqual(request["dataset"], "OPRA.PILLAR")
        self.assertEqual(request["symbols"], ["SPY.OPT"])

    def test_rejects_naive_timestamp(self):
        with self.assertRaisesRegex(ValueError, "UTC offset"):
            MODULE.build_request(
                start="2026-08-03T09:30:00",
                end="2026-08-03T16:00:00-04:00",
                schema="cbbo-1s",
                symbols=["SPY.OPT"],
                stype_in="parent",
            )

    def test_rejects_ranges_over_seven_days(self):
        with self.assertRaisesRegex(ValueError, "cannot exceed 7 days"):
            MODULE.build_request(
                start="2026-08-01T00:00:00Z",
                end="2026-08-09T00:00:01Z",
                schema="cbbo-1s",
                symbols=["SPY.OPT"],
                stype_in="parent",
            )

    def test_cost_path_calls_metadata_only(self):
        client = FakeClient()
        request = {
            "dataset": "OPRA.PILLAR",
            "start": "2026-08-03T09:30:00-04:00",
            "end": "2026-08-03T16:00:00-04:00",
            "symbols": ["SPY.OPT"],
            "schema": "cbbo-1s",
            "stype_in": "parent",
        }
        self.assertAlmostEqual(MODULE.estimate_cost(client, request), 1.2345678)
        self.assertEqual(client.metadata.calls, [request])
        self.assertFalse(hasattr(client, "timeseries"))


if __name__ == "__main__":
    unittest.main()

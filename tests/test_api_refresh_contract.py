"""Regression coverage for the API-to-refresh-worker contract without live services."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


class RefreshComicContractTest(unittest.TestCase):
    def setUp(self):
        source = Path(__file__).parents[1] / "mylar" / "api.py"
        tree = ast.parse(source.read_text())
        api = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "Api")
        method = next(node for node in api.body if isinstance(node, ast.FunctionDef) and node.name == "_refreshComic")
        isolated = ast.Module(body=[method], type_ignores=[])
        self.connection = Mock()
        self.connection.selectone.return_value.fetchone.return_value = {"ComicName": "Captain America", "ComicYear": "2025"}
        self.queue = SimpleNamespace(queue=[], qsize=lambda: len(self.queue.queue))
        self.importer = SimpleNamespace(refresh_thread=Mock())
        namespace = {"db": SimpleNamespace(DBConnection=lambda: self.connection), "mylar": SimpleNamespace(REFRESH_QUEUE=self.queue), "importer": self.importer, "logger": Mock(), "re": __import__("re")}
        exec(compile(isolated, str(source), "exec"), namespace)
        self.subject = SimpleNamespace(data=None, _failureResponse=lambda message: json.dumps({"success": False, "error": message}), _successResponse=lambda message: json.dumps({"success": True, "data": message}))
        self.call = lambda **kwargs: namespace["_refreshComic"](self.subject, **kwargs)

    def test_single_refresh_passes_seriesyear_and_returns_success(self):
        self.call(id="165232")
        self.assertEqual(self.importer.refresh_thread.call_args.args[0], [{"comicid": "165232", "comicname": "Captain America", "seriesyear": "2025"}])
        self.assertTrue(json.loads(self.subject.data)["success"])
        self.assertIn("for ComicID 165232", json.loads(self.subject.data)["data"])

    def test_provider_prefix_is_removed_from_queue_payload(self):
        self.call(id="4050-165232")
        self.assertEqual(self.importer.refresh_thread.call_args.args[0][0]["comicid"], "165232")

    def test_multiple_refresh_response_formats_correctly(self):
        self.call(id="165232,172746")
        self.assertEqual(len(self.importer.refresh_thread.call_args.args[0]), 2)
        self.assertIn("2 items", json.loads(self.subject.data)["data"])

    def test_missing_parameter_is_failure_without_import(self):
        self.call()
        self.assertFalse(json.loads(self.subject.data)["success"])
        self.importer.refresh_thread.assert_not_called()

    def test_unknown_series_is_failure_without_import(self):
        self.connection.selectone.return_value.fetchone.return_value = None
        self.call(id="missing")
        self.assertFalse(json.loads(self.subject.data)["success"])
        self.importer.refresh_thread.assert_not_called()

    def test_multiple_already_queued_ids_do_not_raise_format_error(self):
        self.queue.queue = ["165232", "172746"]
        self.call(id="165232,172746")
        self.assertIn("queue of 2 items", json.loads(self.subject.data)["data"])
        self.importer.refresh_thread.assert_not_called()


if __name__ == "__main__":
    unittest.main()

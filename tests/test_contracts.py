import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("benchmark", ROOT / "scripts/benchmark.py")
assert SPEC is not None and SPEC.loader is not None
benchmark = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark)


class ContractTests(unittest.TestCase):
    def test_dflash2_is_the_default_serving_mode(self):
        self.assertIn('MODE="${MODE:-dflash2}"', (ROOT / "scripts/serve.sh").read_text())

    def test_protocol_counts(self):
        protocol = json.loads((ROOT / "protocol.json").read_text())
        fixtures = json.loads((ROOT / "fixtures.json").read_text())["fixtures"]
        self.assertEqual(set(protocol["arms"]), {"no-spec", "dflash2"})
        self.assertEqual(len(fixtures), 9)
        self.assertEqual(len(fixtures) * protocol["request_contract"]["repetitions_per_fixture"], 27)
        self.assertEqual(protocol["acceptance"]["complete_rows_per_arm"], 27)

    def test_artifact_verifier_accepts_exact_and_rejects_extra(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a").write_bytes(b"abc")
            manifest = {"repository": "x/y", "revision": "a" * 40, "files": [{"name": "a", "bytes": 3, "sha256": hashlib.sha256(b"abc").hexdigest()}]}
            mp = root / "manifest.json"
            mp.write_text(json.dumps(manifest))
            cmd = ["python3", str(ROOT / "scripts/verify_artifacts.py"), "--manifest", str(mp), "--root", str(root)]
            self.assertEqual(subprocess.run(cmd, capture_output=True).returncode, 1)
            mp.unlink()
            mp2 = Path(td).parent / (Path(td).name + "-manifest.json")
            mp2.write_text(json.dumps(manifest))
            try:
                self.assertEqual(subprocess.run(cmd[:3] + [str(mp2)] + cmd[4:], capture_output=True).returncode, 0)
                (root / "extra").write_text("x")
                self.assertEqual(subprocess.run(cmd[:3] + [str(mp2)] + cmd[4:], capture_output=True).returncode, 1)
            finally:
                mp2.unlink(missing_ok=True)

    def test_quality_scorers_reject_numeric_substrings_and_bad_prose(self):
        self.assertFalse(benchmark.score({"id": "math"}, {"content": "15170"})[0])
        self.assertFalse(benchmark.score({"id": "reasoning"}, {"content": "4370", "reasoning_content": "x"})[0])
        bad = "A draft is checked by target verification. This does not increase throughput. It may reduce speed."
        self.assertFalse(benchmark.score({"id": "prose"}, {"content": bad})[0])

    def test_runtime_manifest_binds_resolved_image(self):
        manifest = json.loads((ROOT / "runtime-manifest.json").read_text())
        self.assertRegex(manifest["image_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(manifest["target_revision"], json.loads((ROOT / "manifests/target.json").read_text())["revision"])
        self.assertEqual(manifest["draft_revision"], json.loads((ROOT / "manifests/draft.json").read_text())["revision"])

    def test_mamba_pool_matches_scheduler_ceiling(self):
        serve = (ROOT / "scripts/serve.sh").read_text()
        mamba = re.search(r"--max-mamba-cache-size\s+(\d+)", serve)
        running = re.search(r"--max-running-requests\s+(\d+)", serve)
        assert mamba is not None and running is not None
        self.assertEqual(int(mamba.group(1)), 5 * int(running.group(1)))

    def test_study_and_service_have_disjoint_ownership(self):
        runner = (ROOT / "scripts/run_study.sh").read_text()
        service = (ROOT / "deploy/qwen38-abliterated-dflash2-service.sh").read_text()
        serve = (ROOT / "scripts/serve.sh").read_text()
        self.assertIn("nvfp4-study", runner)
        self.assertIn("OWNER=study", runner)
        self.assertIn("OWNER=systemd:qwen38-abliterated-dflash2", service)
        self.assertIn("io.sxuff.qwen38.owner", serve)

    def test_rollback_requires_identity_and_generation_canary(self):
        runner = (ROOT / "scripts/run_study.sh").read_text()
        self.assertIn("wait_endpoint.py", runner)
        self.assertIn("RESTORE_EXPECTED_MODEL", runner)
        self.assertIn("RESTORE_CANARY_EXPECTED", runner)
        self.assertIn("rollback verification failed", runner)

    def test_historical_seal_rejects_forged_lineage(self):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "repo"
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("private", "__pycache__"))
            seal_path = dst / "preregistration.json"
            seal = json.loads(seal_path.read_text())
            seal["source_commit"] = "0" * 40
            seal["source_git_tree"] = "0" * 40
            seal_path.write_text(json.dumps(seal))
            result = subprocess.run(["python3", str(dst / "scripts/verify_seal.py")], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_contract_rejects_modified_tracked_runner(self):
        with tempfile.TemporaryDirectory() as td:
            dst = Path(td) / "repo"
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns("private", "__pycache__"))
            with (dst / "scripts/benchmark.py").open("a") as f:
                f.write("\n# mutation\n")
            result = subprocess.run(["python3", str(dst / "scripts/verify_contract.py")], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

    def test_dead_endpoint_collector_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "dead.json"
            result = subprocess.run([
                "python3", str(ROOT / "scripts/benchmark.py"), "--arm", "no-spec",
                "--protocol", str(ROOT / "protocol.json"), "--fixtures", str(ROOT / "fixtures.json"),
                "--output", str(out), "--base-url", "http://127.0.0.1:9/v1",
            ], capture_output=True, timeout=60)
            envelope = json.loads(out.read_text())
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(len(envelope["rows"]), 27)
            self.assertEqual(len(envelope["errors"]), 27)
            self.assertTrue(envelope["collection_complete"])
            self.assertFalse(envelope["runtime_success"])
            self.assertFalse(envelope["complete"])

    def _synthetic_analysis(self, quality_pass: bool, dflash_active: bool):
        td = tempfile.TemporaryDirectory()
        root = Path(td.name)
        fixtures = json.loads((ROOT / "fixtures.json").read_text())["fixtures"]
        for arm in ("no-spec", "dflash2"):
            rows = []
            for fixture in fixtures:
                for repetition in range(3):
                    rows.append({
                        "fixture_id": fixture["id"], "repetition": repetition,
                        "performance": fixture["performance"], "quality_pass": quality_pass,
                        "payload_sha256": f"p-{fixture['id']}-{repetition}",
                        "content_sha256": f"c-{fixture['id']}-{repetition}",
                        "usage": {"completion_tokens": 10}, "ttft_seconds": 0.1,
                        "end_to_end_completion_tokens_per_second": 20.0 if arm == "dflash2" else 10.0,
                    })
            (root / f"{arm}.json").write_text(json.dumps({"complete": True, "errors": [], "rows": rows}))
            (root / f"{arm}-telemetry.jsonl").write_text(json.dumps({"mem_available_bytes": 32 * 1024**3, "swap_growth_bytes": 0}) + "\n")
            metrics = ""
            if arm == "dflash2" and dflash_active:
                metrics = "sglang:spec_accept_length 4\nsglang:spec_accept_rate 0.5\nsglang:spec_verify_calls_total 10\n"
            (root / f"{arm}-metrics.txt").write_text(metrics)
        output = root / "summary.json"
        report = root / "report.md"
        result = subprocess.run(["python3", str(ROOT / "scripts/analyze.py"), "--root", str(root), "--output", str(output), "--report", str(report)], capture_output=True)
        return td, result, json.loads(output.read_text()), report.read_text()

    def test_analyzer_enforces_quality_and_dflash_activation(self):
        td, result, summary, report = self._synthetic_analysis(False, True)
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(summary["gate"]["study_passed"])
            self.assertIn("NO-GO", report)
        finally:
            td.cleanup()
        td, result, summary, _ = self._synthetic_analysis(True, False)
        try:
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(summary["gate"]["dflash_active"])
        finally:
            td.cleanup()
        td, result, summary, report = self._synthetic_analysis(True, True)
        try:
            self.assertEqual(result.returncode, 0)
            self.assertTrue(summary["gate"]["study_passed"])
            self.assertIn("PASS", report)
        finally:
            td.cleanup()

    def test_apache_notice_is_distributed(self):
        self.assertTrue((ROOT / "THIRD_PARTY_LICENSES/Apache-2.0.txt").is_file())
        notice = (ROOT / "NOTICE").read_text()
        for rel in json.loads((ROOT / "runtime-manifest.json").read_text())["overlay_files"]:
            self.assertIn("docker/" + rel["path"], notice)


if __name__ == "__main__":
    unittest.main()

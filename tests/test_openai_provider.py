"""Provider transport and workflow integration without external API calls."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from srbench.common.model_provider import ModelCaller, ModelRequestError, build_model_caller
from srbench.generation import batch, data_spec, scenarios

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-5.6-sol"


def response(message=None, **extra):
    return httpx.Response(200, json={
        "model": MODEL, "choices": [{"message": message or {"content": "OK"}}], **extra,
    })


class OpenAIProviderTests(unittest.TestCase):
    def test_openai_uses_selected_credentials_endpoint_model_and_completion_budget(self):
        environment = {"OPENAI_API_KEY": " openai-key ", "OPENAI_BASE_URL": "https://env.invalid/v1",
                       "OPENROUTER_API_KEY": "other-key", "ANTHROPIC_API_KEY": "another-key"}
        for base in ("https://argument.invalid/v1/", "https://argument.invalid/v1/chat/completions/"):
            with self.subTest(base=base), patch.dict(os.environ, environment, clear=True), \
                    patch("srbench.common.model_provider.httpx.post", return_value=response()) as post:
                caller = build_model_caller("openai", base_url=base, auth_source="auth_token")
                self.assertEqual(caller.complete("hello", MODEL, 4000, "system"), "OK")
            self.assertEqual(post.call_args.args[0], "https://argument.invalid/v1/chat/completions")
            sent = post.call_args.kwargs
            self.assertEqual(sent["headers"], {"Authorization": "Bearer openai-key", "Content-Type": "application/json"})
            self.assertEqual(sent["json"], {
                "model": MODEL, "max_completion_tokens": 4000,
                "messages": [{"role": "system", "content": "system"}, {"role": "user", "content": "hello"}],
            })
            self.assertIsNone(caller.anthropic_client)
            self.assertIsNone(caller.openrouter_api_key)

    def test_environment_and_official_default_endpoints(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True):
            self.assertEqual(build_model_caller("openai").openai_base_url, "https://api.openai.com/v1")
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key", "OPENAI_BASE_URL": "https://env.invalid/v1"}, clear=True):
            self.assertEqual(build_model_caller("openai").openai_base_url, "https://env.invalid/v1")

    def test_missing_openai_key_does_not_fall_back_to_other_credentials(self):
        for key in ("", "   "):
            with self.subTest(key=key), patch.dict(os.environ, {
                "OPENAI_API_KEY": key, "ANTHROPIC_API_KEY": "other", "OPENROUTER_API_KEY": "other",
            }, clear=True), self.assertRaisesRegex(SystemExit, "Missing OPENAI_API_KEY"):
                build_model_caller("openai")
        with self.assertRaisesRegex(ValueError, "Unsupported provider"):
            build_model_caller("unknown")

    def test_openrouter_retains_credentials_headers_and_token_parameter(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "router-key", "OPENAI_API_KEY": "other"}, clear=True), \
                patch("srbench.common.model_provider.httpx.post", return_value=response()) as post:
            caller = build_model_caller("openrouter")
            caller.openrouter_chat(messages=[{"role": "user", "content": "hello"}], model="vendor/model", max_tokens=123)
        self.assertEqual(post.call_args.args[0], "https://openrouter.ai/api/v1/chat/completions")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer router-key")
        self.assertIn("HTTP-Referer", post.call_args.kwargs["headers"])
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 123)
        self.assertNotIn("max_completion_tokens", post.call_args.kwargs["json"])

    def test_text_blocks_are_extracted_and_empty_or_malformed_responses_fail(self):
        caller = ModelCaller("openai", openai_api_key="key", openai_base_url="https://api.invalid/v1")
        with patch("srbench.common.model_provider.httpx.post", return_value=response({
            "content": [{"type": "text", "text": "O"}, {"type": "text", "text": "K"}],
        })):
            self.assertEqual(caller.complete("hello", MODEL, 100), "OK")
        for payload in ({"choices": []}, {"choices": [{"message": None}]}, {"choices": [{"message": {"content": None}}]}, []):
            with self.subTest(payload=payload), patch("srbench.common.model_provider.httpx.post", return_value=httpx.Response(200, json=payload)), \
                    self.assertRaises(ModelRequestError):
                caller.complete("hello", MODEL, 100)

    def test_json_mode_applies_to_structured_openai_calls_only(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key", "OPENROUTER_API_KEY": "router"}, clear=True), \
                patch("srbench.common.model_provider.httpx.post", return_value=response({"content": "{}"})) as post:
            caller = build_model_caller("openai")
            self.assertEqual(caller.complete("Return JSON", MODEL, 100, json_mode=True), "{}")
            self.assertEqual(post.call_args.kwargs["json"]["response_format"], {"type": "json_object"})
            caller.chat(messages=[{"role": "user", "content": "use tools"}], model=MODEL, max_tokens=100)
            self.assertNotIn("response_format", post.call_args.kwargs["json"])
            build_model_caller("openrouter").complete("Return JSON", "vendor/model", 100, json_mode=True)
            self.assertNotIn("response_format", post.call_args.kwargs["json"])

    def test_truncated_output_is_not_parsed_as_a_finished_answer_or_tool_call(self):
        caller = ModelCaller("openai", openai_api_key="key", openai_base_url="https://api.invalid/v1")
        for content in ("{}", None):
            with self.subTest(content=content), patch("srbench.common.model_provider.httpx.post", return_value=httpx.Response(200, json={
                "choices": [{"message": {"content": content}, "finish_reason": "length"}],
            })), self.assertRaisesRegex(ModelRequestError, "truncated"):
                caller.chat(messages=[], model=MODEL, max_tokens=100)

    def test_transient_errors_retry_but_auth_errors_fail_immediately_in_transport(self):
        caller = ModelCaller("openai", openai_api_key="key", openai_base_url="https://api.invalid/v1")
        with patch.dict(os.environ, {"SRBENCH_OPENAI_MAX_RETRIES": "1"}), \
                patch("srbench.common.model_provider.time.sleep"), \
                patch("srbench.common.model_provider.httpx.post", side_effect=[httpx.Response(503), response()]) as post:
            self.assertEqual(caller.complete("hello", MODEL, 100), "OK")
            self.assertEqual(post.call_count, 2)
        with patch("srbench.common.model_provider.httpx.post", return_value=httpx.Response(401, json={"error": "invalid key"})) as post, \
                self.assertRaisesRegex(ModelRequestError, "openai HTTP 401"):
            caller.complete("hello", MODEL, 100)
        self.assertEqual(post.call_count, 1)

    def test_scenario_equation_uses_shared_openai_transport(self):
        equation = dict(equation_type="static_explicit", target_symbol="F", expression="-k*x",
                        symbols=["F", "x", "k"], symbol_descriptions=["force", "displacement", "stiffness"],
                        symbol_properties=["O", "V", "P"], derivation_notes="linear spring")
        spec = dict(model_family="static", target_symbol="F", target_description="restoring force",
                    input_symbols=[{"symbol": "x", "range": [0, 2], "description": "displacement"}],
                    expected_behaviors=[], forbidden_behaviors=[])
        with patch.dict(os.environ, {"OPENAI_API_KEY": "key"}, clear=True), \
                patch("srbench.common.model_provider.httpx.post", return_value=response({"content": json.dumps(equation)})) as post:
            result = scenarios.derive_equation(build_model_caller("openai"), "spring", spec, "physics", "classical_mechanics", MODEL)
        self.assertEqual(result["expression"], "-k*x")
        self.assertEqual(post.call_args.kwargs["json"]["model"], MODEL)
        self.assertEqual(post.call_args.kwargs["json"]["response_format"], {"type": "json_object"})

    def test_dataspec_tool_results_reach_next_turn_without_claude_sdk(self):
        record = dict(model_family="static", equation_type="static_explicit", target_symbol="y", expression="a*x",
                      symbols=["y", "x", "a"], symbol_properties=["O", "V", "P"],
                      symbol_descriptions=["response", "input", "coefficient"])
        spec = dict(equation_type="explicit", integrator="evaluate_explicit", dependent_variable="y",
                    independent_variables=[{"symbol": "x", "range": [0, 2], "n_points": 5000}],
                    parameters=[{"symbol": "a", "value": 2}], rhs_for_integrator="a*x", noise=0)
        for provider in ("openai", "openrouter"):
            requests = []

            def respond(url, **kwargs):
                requests.append(copy.deepcopy(kwargs["json"]))
                if len(requests) == 1:
                    name, args = "analyze_expression", {"expression": "a*x", "target_symbol": "y"}
                else:
                    name, args = "emit_data_gen_spec", spec
                return response({"content": None, "tool_calls": [{"id": f"call_{len(requests)}", "type": "function",
                    "function": {"name": name, "arguments": json.dumps(args)}}]})

            with self.subTest(provider=provider), patch.dict(os.environ, {f"{provider.upper()}_API_KEY": "key"}, clear=True), \
                    patch("srbench.common.model_provider.httpx.post", side_effect=respond), \
                    patch.object(data_spec, "plan_data_generation_async", side_effect=AssertionError("Claude SDK must not run")):
                result = data_spec.plan_data_generation(record, "physics", provider=provider, model=MODEL,
                    base_url="https://argument.invalid/v1/chat/completions", cli_path="/missing/claude", max_turns=2, verbose=False)
            self.assertEqual(result["_provider"], provider)
            self.assertEqual(result["rhs_for_integrator"], "a*x")
            self.assertEqual(result["_num_turns"], 2)
            self.assertEqual(requests[1]["messages"][-2]["tool_calls"][0]["id"], "call_1")
            feedback = requests[1]["messages"][-1]
            self.assertEqual((feedback["role"], feedback["tool_call_id"]), ("tool", "call_1"))
            self.assertIn("free_symbols", json.loads(feedback["content"]))
            self.assertEqual({tool["function"]["name"] for tool in requests[0]["tools"]},
                             {"analyze_expression", "check_substitution", "emit_data_gen_spec"})
            self.assertTrue(all(request["model"] == MODEL for request in requests))

    def test_generate_cli_propagates_openai_and_model_into_both_stages(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as output:
            batch.main(["--run-name", "dry", "--output-dir", tmp, "--subjects", "biology", "physics",
                        "--provider", "openai", "--model", MODEL, "--base-url", "https://example.invalid/v1", "--dry-run"])
            plan = json.loads(output.getvalue())
            self.assertFalse((Path(tmp) / "dry").exists())
        args = SimpleNamespace(**plan["config"])
        commands = plan["first_round_commands"] + [batch.evolution_command(
            args, "biology", 0, 0, Path("equations.jsonl"), "equation_1", Path("evolved"))]
        for command in commands:
            self.assertEqual(command[command.index("--provider") + 1], "openai")
            self.assertEqual(command[command.index("--model") + 1], MODEL)
            self.assertEqual(command[command.index("--base-url") + 1], "https://example.invalid/v1")

    def test_all_generation_cli_help_advertises_openai(self):
        for module in ("batch", "scenarios", "pipeline", "evolution", "novelty", "data_spec"):
            with self.subTest(module=module):
                result = subprocess.run([sys.executable, "-m", f"srbench.generation.{module}", "--help"],
                                        cwd=ROOT, text=True, capture_output=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("{anthropic,openrouter,openai}", result.stdout)


if __name__ == "__main__":
    unittest.main()

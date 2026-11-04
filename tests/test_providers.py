import http.client
import io
import json
import ssl
import traceback
import unittest
from unittest.mock import ANY, patch

from looksy import providers


KEY = "fixture-header-only"
PROMPT = "  Draft a short report.\n"
MESSAGES = [{"role": "user", "content": PROMPT}]


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.connect = self.enterContext(patch("looksy.providers.http.client.HTTPSConnection"))
        self.connection = self.connect.return_value
        self.response = self.connection.getresponse.return_value
        self.response.status = 200

    def set_reply(self, body):
        self.response.read.side_effect = io.BytesIO(body).read

    def assert_contract(self, provider, model, host, path, headers, payload, reply):
        self.set_reply(json.dumps(reply).encode())
        result = providers.ask(provider, KEY, model, PROMPT)
        self.assertEqual(result, "First.\nSecond.")
        self.connect.assert_called_once_with(host, timeout=30, context=ANY)
        context = self.connect.call_args.kwargs["context"]
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)
        self.connection.request.assert_called_once()
        method, actual_path = self.connection.request.call_args.args
        kwargs = self.connection.request.call_args.kwargs
        self.assertEqual((method, actual_path), ("POST", path))
        self.assertEqual(json.loads(kwargs["body"]), payload)
        self.assertNotIn(KEY, actual_path)
        self.assertNotIn(KEY.encode(), kwargs["body"])
        self.assertEqual(kwargs["headers"], {"Content-Type": "application/json", **headers})
        self.response.read.assert_called_once_with(256 * 1024 + 1)
        self.connection.close.assert_called_once()

    def test_anthropic_messages(self):
        self.assert_contract(
            "anthropic", "claude-sonnet-4-6", "api.anthropic.com", "/v1/messages",
            {"Authorization": "Bearer " + KEY, "anthropic-version": "2026-10-21"},
            {"model": "claude-sonnet-4-6", "messages": MESSAGES, "max_tokens": 1024},
            {"stop_reason": "end_turn", "content": [
                {"type": "thinking", "thinking": "hidden"},
                {"type": "text", "text": "First."}, {"type": "text", "text": "Second."}]},
        )

    def test_openai_responses(self):
        self.assert_contract(
            "openai", "gpt-4.1-mini", "api.openai.com", "/v1/responses",
            {"Authorization": "Bearer " + KEY},
            {"model": "gpt-4.1-mini", "input": PROMPT, "max_output_tokens": 1024, "store": False},
            {"status": "completed", "output": [
                {"type": "reasoning", "summary": []},
                {"type": "message", "role": "assistant", "content": [
                    {"type": "output_text", "text": "First."},
                    {"type": "output_text", "text": "Second."}]}]},
        )

    def test_openrouter_chat_completion(self):
        self.assert_contract(
            "openrouter", "vendor/model:free", "openrouter.ai", "/api/v1/chat/completions",
            {"Authorization": "Bearer " + KEY},
            {"model": "vendor/model:free", "messages": MESSAGES, "max_tokens": 1024,
             "provider": {"allow_fallbacks": False, "require_parameters": True}},
            {"choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "First.\nSecond."}}]},
        )

    def test_gemini_generate_content(self):
        self.assert_contract(
            "gemini", "gemini-2.5-flash", "generativelanguage.googleapis.com",
            "/v1beta/models/gemini-2.5-flash:generateContent", {"x-goog-api-key": KEY},
            {"contents": [{"role": "user", "parts": [{"text": PROMPT}]}],
             "generationConfig": {"maxOutputTokens": 1024}},
            {"candidates": [{"finishReason": "STOP", "content": {"role": "model", "parts": [
                {"thought": True, "text": "hidden"}, {"text": "First."}, {"text": "Second."}]}}]},
        )

    def test_inputs_rejected_before_network(self):
        invalid = [
            ("unknown", KEY, "model", PROMPT), ([], KEY, "model", PROMPT),
            ("openai", "", "model", PROMPT), ("anthropic", "key\nAnother: value", "model", PROMPT),
            ("gemini", KEY, "model", " \n"), ("gemini", KEY, "model", "£" * 16385),
            ("openai", KEY, "model", "\ud800"), ("gemini", "k" * 4097, "model", PROMPT),
            ("gemini", KEY, "models/gemini-name", PROMPT),
            ("openrouter", KEY, "vendor/model:online", PROMPT),
        ]
        for provider in ("gemini", "openrouter", "openai", "anthropic"):
            for model in ("https://evil.example", "../model", "a/b/../c", "bad%2Fpath",
                          "a?key=x", "a\\b", "m#fragment", "a\r\n", "/a", "a" * 201):
                invalid.append((provider, KEY, model, PROMPT))
        for args in invalid:
            with self.subTest(args=args[:1]), self.assertRaises(providers.ProviderError):
                providers.ask(*args)
        self.connect.assert_not_called()

    def test_redirects_and_http_errors_never_read_body_or_retry(self):
        self.response.getheader.return_value = "https://elsewhere.invalid/"
        for code in (301, 302, 303, 307, 308, 400, 401, 429, 500):
            with self.subTest(code=code):
                self.response.status = code
                with self.assertRaises(providers.ProviderError) as raised:
                    providers.ask("openai", KEY, "model", PROMPT)
                self.assertIn(str(code), str(raised.exception))
                self.assertNotIn(KEY, str(raised.exception))
        self.assertEqual(self.connect.call_count, 9)
        self.assertEqual(self.connection.request.call_count, 9)
        self.assertEqual(self.connection.close.call_count, 9)
        self.response.read.assert_not_called()

    def test_transport_failure_is_sanitized_and_not_retried(self):
        for failure in (OSError, http.client.HTTPException):
            with self.subTest(failure=failure):
                self.connection.getresponse.side_effect = failure(KEY + PROMPT)
                try:
                    providers.ask("gemini", KEY, "model", PROMPT)
                except providers.ProviderError:
                    diagnostic = traceback.format_exc()
                else:
                    self.fail("Expected a provider error")
                self.assertNotIn(KEY, diagnostic)
                self.assertNotIn(PROMPT, diagnostic)
        self.assertEqual(self.connection.request.call_count, 2)
        self.assertEqual(self.connection.close.call_count, 2)

    def test_invalid_response_is_sanitized(self):
        for body in (b"not-json " + PROMPT.encode(), b"\xff", b"[" * 2000 + b"]" * 2000,
                     b"false", b'{"error":{"message":"fixture-header-only"}}',
                     b"x" * (256 * 1024 + 1)):
            self.set_reply(body)
            with self.assertRaises(providers.ProviderError) as raised:
                providers.ask("openai", KEY, "model", PROMPT)
            self.assertNotIn(KEY, str(raised.exception))
            self.assertNotIn(PROMPT, str(raised.exception))

    def test_empty_truncated_or_unsafe_responses_rejected(self):
        replies = [
            ("openai", {"status": "incomplete", "output": [{"type": "message", "role": "assistant",
                        "content": [{"type": "output_text", "text": "partial"}]}]}),
            ("openai", {"status": "completed", "output": [{"type": "message", "role": "assistant",
                        "content": [{"type": "output_text", "text": "answer " + KEY}]}]}),
            ("openrouter", {"choices": [{"finish_reason": "length", "message": {"role": "assistant", "content": "partial"}}]}),
            ("anthropic", {"stop_reason": "max_tokens", "content": [{"type": "text", "text": "partial"}]}),
            ("anthropic", {"stop_reason": "end_turn", "content": [{"type": "text", "text": "x" * 16385}]}),
            ("anthropic", {"stop_reason": "end_turn", "content": [{"type": "text", "text": "\ud800"}]}),
            ("gemini", {"candidates": [{"finishReason": "SAFETY", "content": {"parts": [{"text": "partial"}]}}]}),
            ("gemini", {"candidates": []}),
        ]
        for provider, reply in replies:
            with self.subTest(provider=provider):
                self.set_reply(json.dumps(reply).encode())
                with self.assertRaises(providers.ProviderError):
                    providers.ask(provider, KEY, "vendor/model" if provider == "openrouter" else "model", PROMPT)

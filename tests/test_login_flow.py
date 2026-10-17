import ssl
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from bebraland_frontend.api import WebSocketApiError, WebSocketClosed
from bebraland_frontend.app import Bridge, LauncherWindow


class LoginFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tasks = []
        self.bridge = Bridge()
        self.window = SimpleNamespace(
            _login_running=False,
            login_error=False,
            login_status="",
            two_factor_visible=False,
            _last_login_email="",
            _last_login_password="",
            client=Mock(),
            bridge=self.bridge,
            refresh_state=Mock(),
            reset_client=Mock(),
            run_bg=self.tasks.append,
        )
        self.popup = Mock()
        self.bridge.error.connect(self.popup)
        self.bridge.login_failed.connect(lambda message: LauncherWindow.handle_login_failed(self.window, message))
        self.bridge.two_factor.connect(lambda message: LauncherWindow.show_two_factor(self.window, message))

    def login(self, code: str = "") -> None:
        LauncherWindow.login(self.window, "test-user", "test-password", code)

    def test_repeat_submit_is_blocked_while_login_is_running(self) -> None:
        self.login()
        self.login()
        self.assertEqual(len(self.tasks), 1)
        self.assertTrue(self.window._login_running)
        self.assertEqual(self.window.login_status, "Logging in...")

    def test_network_failure_is_inline_and_allows_retry(self) -> None:
        for error in (ssl.SSLEOFError("TLS ended"), WebSocketClosed("Disconnected"), TimeoutError()):
            with self.subTest(error=type(error).__name__):
                self.window.client.azuriom_login.side_effect = error
                self.login()
                self.tasks[-1]()
                self.assertFalse(self.window._login_running)
                self.assertTrue(self.window.login_error)
                self.assertIn("Please try again", self.window.login_status)
                self.assertNotEqual(self.window.login_status, "Logging in...")
                self.popup.assert_not_called()
        self.assertEqual(self.window.client.azuriom_login.call_count, 3)

    def test_wrong_password_message_is_preserved(self) -> None:
        self.window.client.azuriom_login.side_effect = WebSocketApiError(401, {"message": "Invalid credentials"})
        self.login()
        self.tasks[-1]()
        self.assertEqual(self.window.login_status, "Invalid credentials")
        self.assertFalse(self.window._login_running)
        self.popup.assert_not_called()

    def test_pending_two_factor_allows_code_submission(self) -> None:
        self.window.client.azuriom_login.return_value = {"status": "pending", "message": "2FA code required"}
        self.login()
        self.tasks[-1]()
        self.assertTrue(self.window.two_factor_visible)
        self.assertFalse(self.window._login_running)
        self.assertFalse(self.window.login_error)
        self.login("123456")
        self.assertTrue(self.window._login_running)
        self.assertEqual(len(self.tasks), 2)

    def test_two_factor_error_response_allows_code_submission(self) -> None:
        self.window.client.azuriom_login.side_effect = WebSocketApiError(403, {"reason": "2fa", "message": "2FA required"})
        self.login()
        self.tasks[-1]()
        self.assertTrue(self.window.two_factor_visible)
        self.assertFalse(self.window._login_running)
        self.popup.assert_not_called()

    def test_invalid_form_does_not_start_a_request(self) -> None:
        LauncherWindow.login(self.window, "", "", "")
        self.assertTrue(self.window.login_error)
        self.assertFalse(self.window._login_running)
        self.assertEqual(self.tasks, [])


if __name__ == "__main__":
    unittest.main()

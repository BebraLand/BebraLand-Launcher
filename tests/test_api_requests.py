import base64
import hashlib
import json
import threading
import unittest
from unittest.mock import Mock, patch

from bebraland_frontend.api import ApiClient, WebSocketClosed, WebSocketConnection


class ApiRequestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ApiClient("https://example.invalid")
        self.socket = Mock()
        self.client._ws = self.socket
        self.client._ensure_connected = Mock()

    def reply(self, message: dict) -> None:
        self.client._handle_message(
            {"id": message["id"], "type": "response", "ok": True, "result": {"status": "ok"}}
        )

    def test_slow_profiles_do_not_disconnect_pending_login(self) -> None:
        profiles_sent = threading.Event()
        login_sent = threading.Event()
        profiles_finished = threading.Event()
        errors = []

        def send(message: dict) -> None:
            if message["type"] == "profiles.check":
                profiles_sent.set()
            else:
                login_sent.set()
                self.assertTrue(profiles_finished.wait(2))
                self.reply(message)

        def profiles() -> None:
            try:
                self.client._request("profiles.check", {}, timeout=0.05)
            except Exception as exc:
                errors.append(exc)
            finally:
                profiles_finished.set()

        self.socket.send_json.side_effect = send
        worker = threading.Thread(target=profiles, daemon=True)
        worker.start()
        self.assertTrue(profiles_sent.wait(2))
        try:
            result = self.client._request("auth.azuriom.login", {}, timeout=2)
        finally:
            worker.join(2)
        self.assertTrue(login_sent.is_set())
        self.assertEqual(result, {"status": "ok"})
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], TimeoutError)
        self.assertIs(self.client._ws, self.socket)
        self.socket.close.assert_not_called()
        self.assertEqual(self.socket.send_json.call_count, 2)

    def test_late_response_after_timeout_is_discarded(self) -> None:
        with self.assertRaises(TimeoutError):
            self.client._request("profiles.check", {}, timeout=0)
        self.reply(self.socket.send_json.call_args.args[0])
        self.assertEqual(self.client._responses, {})
        self.assertEqual(self.client._pending_requests, set())
        self.socket.close.assert_not_called()

    def test_old_request_cannot_close_reconnected_socket(self) -> None:
        replacement = Mock()
        replacement.send_json.side_effect = self.reply

        def disconnect(message: dict) -> None:
            self.client._ws = replacement
            raise WebSocketClosed("Old connection failed")

        self.socket.send_json.side_effect = disconnect
        result = self.client._request("ping", {}, timeout=1)
        self.assertEqual(result, {"status": "ok"})
        self.assertIs(self.client._ws, replacement)
        replacement.close.assert_not_called()

    def test_request_retries_when_its_connection_has_been_replaced(self) -> None:
        replacement = Mock()
        replacement.send_json.side_effect = self.reply
        self.socket.send_json.side_effect = lambda message: setattr(self.client, "_ws", replacement)
        result = self.client._request("ping", {}, timeout=0.05)
        self.assertEqual(result, {"status": "ok"})
        replacement.close.assert_not_called()


class WebSocketHandshakeTests(unittest.TestCase):
    def test_greeting_in_handshake_packet_is_not_lost(self) -> None:
        greeting = {"type": "hello", "site_url": "https://new.example"}
        payload = json.dumps(greeting).encode()
        frame = bytes([0x81, len(payload)]) + payload
        socket = Mock()
        incoming = bytearray()

        def send(request: bytes) -> None:
            headers = request.decode().split("\r\n")
            key = next(line.split(": ", 1)[1] for line in headers if line.startswith("Sec-WebSocket-Key:"))
            accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
            incoming.extend(f"HTTP/1.1 101 Switching Protocols\r\nSec-WebSocket-Accept: {accept}\r\n\r\n".encode() + frame)

        def receive(size: int) -> bytes:
            result = bytes(incoming[:size])
            del incoming[:size]
            return result

        socket.sendall.side_effect = send
        socket.recv.side_effect = receive
        with patch("bebraland_frontend.api.socket.create_connection", return_value=socket):
            connection = WebSocketConnection("ws://backend.example/api/v1/ws")
            connection.connect()
            self.assertEqual(connection.recv_json(), greeting)


if __name__ == "__main__":
    unittest.main()

import importlib.util
import os
from pathlib import Path
import runpy
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from bebraland_frontend import config
from bebraland_frontend.api import ApiClient
from bebraland_frontend.app import LauncherWindow


class SiteUrlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(os.environ, {}, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_one_override_controls_website_and_news(self) -> None:
        os.environ["AZURIOM_URL"] = "https://new.example/bebraland/"
        os.environ["BEBRALAND_SITE_URL"] = "https://old.example"
        self.assertEqual(config.site_url(), "https://new.example/bebraland")
        self.assertEqual(config.news_api_url(), "https://new.example/bebraland/api/posts")

    def test_build_fallback_and_news_endpoint_override(self) -> None:
        with patch.object(config, "build_info", SimpleNamespace(SITE_URL="https://build.example/")):
            self.assertEqual(config.site_url(), "https://build.example")
            self.assertEqual(config.news_api_url(), "https://build.example/api/posts")
        os.environ["BEBRALAND_NEWS_API_URL"] = "https://news.example/feed"
        self.assertEqual(config.news_api_url("https://server.example"), "https://news.example/feed")

    def test_backend_greeting_updates_website_and_reload_news(self) -> None:
        window = SimpleNamespace(_site_url="https://old.example", news=[{"title": "Old news"}], refresh_state=Mock(), fetch_news=Mock())
        client = ApiClient("https://backend.example")
        client.set_event_handlers(site_url_changed=lambda url: LauncherWindow.set_site_url(window, url))
        client._handle_message({"type": "hello", "site_url": "https://new.example/"})
        self.assertEqual(window._site_url, "https://new.example")
        self.assertEqual(window.news, [])
        window.refresh_state.assert_called_once()
        window.fetch_news.assert_called_once()
        self.assertEqual(config.news_api_url(window._site_url), "https://new.example/api/posts")

    def test_explicit_frontend_override_wins_over_server(self) -> None:
        os.environ["AZURIOM_URL"] = "https://local.example"
        window = SimpleNamespace(_site_url=config.site_url(), refresh_state=Mock(), fetch_news=Mock())
        LauncherWindow.set_site_url(window, "https://server.example")
        self.assertEqual(window._site_url, "https://local.example")
        window.fetch_news.assert_not_called()

    def test_old_backend_or_invalid_url_does_not_replace_fallback(self) -> None:
        window = SimpleNamespace(_site_url="https://fallback.example", refresh_state=Mock(), fetch_news=Mock())
        client = ApiClient("https://backend.example")
        client.set_event_handlers(site_url_changed=lambda url: LauncherWindow.set_site_url(window, url))
        for greeting in ({"type": "hello"}, {"type": "hello", "site_url": ""}, {"type": "hello", "site_url": "file:///secret"}):
            client._handle_message(greeting)
        self.assertEqual(window._site_url, "https://fallback.example")
        window.fetch_news.assert_not_called()

    def test_news_from_previous_domain_is_ignored(self) -> None:
        window = SimpleNamespace(_site_url="https://new.example", news=[], refresh_state=Mock())
        LauncherWindow.set_news(window, "https://old.example/api/posts", [{"title": "Old news"}])
        self.assertEqual(window.news, [])
        posts = [{"title": "Current news"}]
        LauncherWindow.set_news(window, "https://new.example/api/posts", posts)
        self.assertEqual(window.news, posts)

    def test_build_metadata_preserves_site_url(self) -> None:
        script = Path(__file__).resolve().parents[1] / "scripts" / "write_build_info.py"
        spec = importlib.util.spec_from_file_location("write_build_info_test", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with TemporaryDirectory() as directory:
            output = Path(directory) / "build_info.py"
            with patch.object(module, "BUILD_INFO", output):
                module.write_build_info("1.0.0", "", "", "https://backend.example", "https://site.example")
            self.assertEqual(runpy.run_path(str(output))["SITE_URL"], "https://site.example")


if __name__ == "__main__":
    unittest.main()

import os
from pathlib import Path
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Property, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QEnterEvent, QMouseEvent, QWheelEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from bebraland_frontend.app import format_post_date
from bebraland_frontend.theme import register_fonts


class Controller(QObject):
    stateChanged = Signal()

    def __init__(self, state):
        super().__init__()
        self.data = state
        self.urls = []

    @Property("QVariant", notify=stateChanged)
    def state(self):
        return self.data

    @Slot(str)
    def openUrl(self, url):
        self.urls.append(url)


def visual_items(item):
    yield item
    for child in item.childItems():
        yield from visual_items(child)


class HomeUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.posts = [
            {"title": f"News item {i}", "description": "An update from the community with enough detail to wrap onto a second line.", "date": "29 Sep 2026", "url": f"https://example.invalid/news/{i}"}
            for i in range(5)
        ]
        profile = {"slug": "test", "name": "Test pack", "minecraft_version": "1.21.1", "description": "Test pack", "launch_allowed": True}
        self.controller = Controller({
            "authenticated": True, "bootstrapping": False, "version": "test", "assetsUrl": "",
            "defaultBackgroundUrl": "", "profiles": [profile], "selectedProfile": profile,
            "selectedSlug": "test", "hasSelectedProfile": True, "optionalMods": [],
            "playDisabled": False, "minecraftRunning": False, "operationRunning": False,
            "offlineMode": False, "progressVisible": False, "updateNotice": {"visible": False},
            "news": self.posts, "siteUrl": "https://example.invalid", "skinBodyUrl": "",
            "accountName": "Test", "status": "Ready",
        })
        self.view = QQuickWidget()
        register_fonts(self.view)
        self.view.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        self.view.resize(1000, 600)
        self.view.rootContext().setContextProperty("controller", self.controller)
        source = Path(__file__).resolve().parents[1] / "resources/qml/Main.qml"
        self.view.setSource(QUrl.fromLocalFile(str(source)))
        self.assertEqual(self.view.status(), QQuickWidget.Status.Ready, self.view.errors())
        self.root = self.view.rootObject()
        self.view.show()
        QTest.qWait(40)

    def tearDown(self):
        self.view.setSource(QUrl())
        self.view.close()
        self.view.deleteLater()
        self.app.processEvents()

    def item(self, name):
        found = self.root.findChild(QQuickItem, name)
        self.assertIsNotNone(found, name)
        return found

    def move_pointer(self, x, y):
        local = QPointF(x, y)
        screen = QPointF(self.view.mapToGlobal(QPoint(x, y)))
        QApplication.sendEvent(self.view, QEnterEvent(local, local, screen))
        QApplication.sendEvent(self.view, QMouseEvent(
            QEvent.Type.MouseMove, local, screen, Qt.MouseButton.NoButton,
            Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier,
        ))
        self.app.processEvents()

    def hovered_shapes(self):
        return [item.property("cursorShape") for item in visual_items(self.root) if item.property("containsMouse")]

    def test_news_stays_inside_window_above_website(self):
        for width, height in ((1000, 600), (1280, 720), (1600, 900)):
            with self.subTest(size=(width, height)):
                self.view.resize(width, height)
                QTest.qWait(20)
                listing = self.item("newsList")
                heading = self.item("newsHeading")
                website = self.item("websiteButton")
                self.assertGreaterEqual(heading.mapToScene(QPointF()).y(), 44)
                self.assertLess(listing.mapToScene(QPointF(0, listing.height())).y(), website.mapToScene(QPointF()).y())
                self.assertLessEqual(website.mapToScene(QPointF(website.width(), website.height())).y(), height)
                self.assertTrue(listing.clip())

    def test_wheel_scroll_reaches_news_without_moving_website(self):
        listing = self.item("newsList")
        website = self.item("websiteButton")
        footer_position = website.mapToScene(QPointF())
        self.assertGreater(listing.property("contentHeight"), listing.height())
        position = listing.mapToScene(QPointF(listing.width() / 2, listing.height() / 2))
        event = QWheelEvent(position, QPointF(self.view.mapToGlobal(position.toPoint())), QPoint(), QPoint(0, -120), Qt.MouseButton.NoButton, Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(self.view, event)
        QTest.qWait(80)
        self.assertGreater(listing.property("contentY"), 0)
        self.assertEqual(website.mapToScene(QPointF()), footer_position)
        listing.setProperty("contentY", listing.property("contentHeight") - listing.height())
        QTest.qWait(30)
        title = next(item for item in visual_items(self.root) if item.objectName() == "newsTitle" and item.property("text") == "News item 4")
        card = title.parentItem().parentItem()
        center = card.mapToScene(QPointF(card.width() / 2, card.height() / 2)).toPoint()
        QTest.mouseClick(self.view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, center)
        self.assertEqual(self.controller.urls, [self.posts[-1]["url"]])

    def test_long_titles_and_descriptions_wrap_inside_cards(self):
        self.controller.data["news"] = [{"title": "A very long news headline " * 12, "description": "A long description " * 30, "date": "29 Sep 2026", "url": "https://example.invalid"}]
        self.controller.stateChanged.emit()
        QTest.qWait(30)
        labels = [item for item in visual_items(self.root) if item.objectName() in {"newsTitle", "newsDescription"}]
        self.assertEqual(len(labels), 2)
        for label in labels:
            self.assertEqual(label.property("lineCount"), 2)
            card = label.parentItem().parentItem()
            self.assertLess(label.mapToItem(card, QPointF(0, label.height())).y(), card.height())

    def test_back_replaces_hovered_button_with_arrow_background(self):
        for page in ("profile", "mods", "profile"):
            with self.subTest(page=page):
                self.root.setProperty("currentPage", page)
                QTest.qWait(20)
                self.move_pointer(180, 60)
                self.assertIn(Qt.CursorShape.PointingHandCursor, self.hovered_shapes())
                QTest.mouseClick(self.view, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, QPoint(180, 60))
                QTest.qWait(20)
                self.assertEqual(self.root.property("currentPage"), "home")
                self.assertEqual(self.hovered_shapes(), [Qt.CursorShape.ArrowCursor])
                self.move_pointer(450, 100)
                self.assertEqual(self.hovered_shapes(), [Qt.CursorShape.ArrowCursor])
                website = self.item("websiteButton")
                center = website.mapToScene(QPointF(website.width() / 2, website.height() / 2))
                self.move_pointer(round(center.x()), round(center.y()))
                self.assertIn(Qt.CursorShape.PointingHandCursor, self.hovered_shapes())


class NewsDateTests(unittest.TestCase):
    def test_iso_timestamps_become_readable_dates(self):
        self.assertEqual(format_post_date("2026-09-29T19:09:01+03:00"), "29 Sep 2026")
        self.assertEqual(format_post_date("2026-07-08T14:10:56Z"), "08 Jul 2026")
        self.assertEqual(format_post_date("2026-06-19T23:49:11-04:00"), "19 Jun 2026")

    def test_empty_and_invalid_dates_are_hidden(self):
        self.assertEqual(format_post_date(None), "")
        self.assertEqual(format_post_date("invalid-date"), "")


if __name__ == "__main__":
    unittest.main()

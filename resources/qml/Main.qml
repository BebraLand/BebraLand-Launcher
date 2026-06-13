import QtQuick
import QtQuick.Controls
import "components"
import "pages"

Rectangle {
    id: root

    width: 1000
    height: 600
    radius: 5
    clip: true
    color: theme.background

    property var s: controller.state || ({})
    property string currentPage: ""

    Theme { id: theme }

    function syncPage() {
        if (!s.authenticated) {
            currentPage = "login"
            return
        }
        if (currentPage === "" || currentPage === "login")
            currentPage = "home"
    }

    Component.onCompleted: syncPage()

    Connections {
        target: controller
        function onStateChanged() {
            root.s = controller.state || ({})
            root.syncPage()
        }
    }

    Image {
        anchors.fill: parent
        source: root.currentPage === "home" && root.s.selectedProfile && root.s.selectedProfile.background_url
                ? root.s.selectedProfile.background_url
                : root.s.defaultBackgroundUrl
        fillMode: Image.PreserveAspectCrop
        asynchronous: true
        cache: false
    }

    Rectangle {
        anchors.fill: parent
        gradient: Gradient {
            GradientStop { position: 0.00; color: "#30000000" }
            GradientStop { position: 0.30; color: "#B80E0E0E" }
            GradientStop { position: 1.00; color: "#F20E0E0E" }
        }
    }

    MouseArea {
        z: 20
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: root.s.authenticated ? 130 : 20
        anchors.rightMargin: 150
        height: 44
        acceptedButtons: Qt.LeftButton
        onPressed: controller.startWindowMove()
    }

    Loader {
        id: pageLoader
        z: 5
        anchors.fill: parent
        sourceComponent: root.currentPage === "login" ? loginComponent
                       : root.currentPage === "settings" ? settingsComponent
                       : root.currentPage === "profile" ? profileComponent
                       : root.currentPage === "mods" ? modsComponent
                       : homeComponent
    }

    Sidebar {
        z: 10
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        visible: root.s.authenticated
        state: root.s
        page: root.currentPage
        onPageRequested: function(page) { root.currentPage = page }
    }

    Rectangle {
        z: 30
        visible: root.s.progressVisible
        anchors.top: parent.top
        anchors.topMargin: 18
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(520, parent.width - 220)
        height: 54
        radius: 18
        color: theme.frame
        border.color: theme.frameBorder
        border.width: 1

        Text {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            text: root.s.progressText || root.s.status || ""
            color: theme.headline
            elide: Text.ElideRight
            font.family: theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.Bold
        }

        Rectangle {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            anchors.bottomMargin: 12
            height: 6
            radius: 3
            color: theme.formBorder

            Rectangle {
                height: parent.height
                radius: parent.radius
                color: theme.primary
                width: parent.width * Math.max(0, Math.min(1, (root.s.progressValue || 0) / Math.max(1, root.s.progressMaximum || 1)))
            }
        }
    }

    Row {
        z: 40
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.rightMargin: 10
        height: 42

        Item {
            width: 46
            height: 42
            Rectangle {
                anchors.centerIn: parent
                width: 11
                height: 1
                color: theme.headline
                opacity: minimizeMouse.containsMouse ? 1 : 0.75
            }
            MouseArea {
                id: minimizeMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: controller.windowMinimize()
            }
        }

        Item {
            width: 46
            height: 42
            Rectangle {
                anchors.centerIn: parent
                width: 11
                height: 11
                color: "transparent"
                border.color: theme.headline
                border.width: 1
                opacity: maxMouse.containsMouse ? 1 : 0.75
            }
            MouseArea {
                id: maxMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: controller.windowMaximize()
            }
        }

        Item {
            width: 46
            height: 42
            Text {
                anchors.centerIn: parent
                text: "x"
                color: theme.headline
                opacity: closeMouse.containsMouse ? 1 : 0.75
                font.family: theme.fontFamily
                font.pixelSize: 18
                font.weight: Font.Light
            }
            MouseArea {
                id: closeMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: controller.windowClose()
            }
        }
    }

    Component {
        id: loginComponent
        LoginPage {
            anchors.fill: parent
            state: root.s
        }
    }

    Component {
        id: homeComponent
        HomePage {
            anchors.fill: parent
            state: root.s
            onNavigate: function(page) { root.currentPage = page }
        }
    }

    Component {
        id: settingsComponent
        SettingsPage {
            anchors.fill: parent
            state: root.s
            onNavigate: function(page) { root.currentPage = page }
        }
    }

    Component {
        id: profileComponent
        ProfilePage {
            anchors.fill: parent
            state: root.s
            onNavigate: function(page) { root.currentPage = page }
        }
    }

    Component {
        id: modsComponent
        ModsPage {
            anchors.fill: parent
            state: root.s
            onNavigate: function(page) { root.currentPage = page }
        }
    }
}

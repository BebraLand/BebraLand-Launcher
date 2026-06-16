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
        if (s.bootstrapping)
            return
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
        source: !root.s.bootstrapping && root.currentPage === "home" && root.s.selectedProfile && root.s.selectedProfile.background_url
                ? root.s.selectedProfile.background_url
                : root.s.defaultBackgroundUrl
        fillMode: Image.PreserveAspectCrop
        asynchronous: false
        cache: true
        smooth: true
        mipmap: true
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
        id: titleDragArea
        z: 20
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.leftMargin: 0
        anchors.rightMargin: 150
        height: 44
        acceptedButtons: Qt.LeftButton
        onPressed: function(mouse) {
            var point = titleDragArea.mapToItem(root, mouse.x, mouse.y)
            controller.startWindowMove(point.x, point.y)
        }
    }

    Loader {
        id: pageLoader
        z: 5
        anchors.fill: parent
        active: !root.s.bootstrapping
        visible: active
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
        visible: root.s.authenticated && !root.s.bootstrapping
        state: root.s
        page: root.currentPage
        onPageRequested: function(page) { root.currentPage = page }
    }

    Item {
        z: 25
        anchors.fill: parent
        visible: root.s.bootstrapping

        Column {
            anchors.centerIn: parent
            spacing: 20

            SharpImage {
                width: 74
                height: 74
                anchors.horizontalCenter: parent.horizontalCenter
                source: root.s.assetsUrl ? root.s.assetsUrl + "/Images/logo.svg" : ""
                renderScale: 1
            }

            Text {
                width: 420
                horizontalAlignment: Text.AlignHCenter
                text: "Connecting to server..."
                color: theme.headline
                elide: Text.ElideRight
                font.family: theme.fontFamily
                font.pixelSize: 18
                font.weight: Font.Bold
            }

            Rectangle {
                width: 180
                height: 5
                radius: 3
                anchors.horizontalCenter: parent.horizontalCenter
                color: theme.formBorder
                clip: true

                Rectangle {
                    id: loadingFill
                    width: 70
                    height: parent.height
                    radius: parent.radius
                    color: theme.primary
                    x: -70
                }

                NumberAnimation {
                    id: loadingAnim
                    target: loadingFill
                    property: "x"
                    from: -70
                    to: 180
                    duration: 1150
                    loops: Animation.Infinite
                    running: root.s.bootstrapping
                }
            }
        }
    }

    Rectangle {
        z: 30
        visible: root.s.progressVisible
        anchors.top: parent.top
        anchors.topMargin: 18
        anchors.horizontalCenter: parent.horizontalCenter
        width: Math.min(520, parent.width - 220)
        height: 66
        radius: 18
        color: theme.frame
        border.color: theme.frameBorder
        border.width: 1

        Text {
            id: progressTitle
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.leftMargin: 18
            anchors.rightMargin: root.s.canCancelDownload ? 96 : 18
            text: root.s.progressTitle || root.s.progressText || root.s.status || ""
            color: theme.headline
            elide: Text.ElideRight
            font.family: theme.fontFamily
            font.pixelSize: 12
            font.weight: Font.Bold
        }

        Rectangle {
            id: progressCancel
            visible: root.s.canCancelDownload
            anchors.top: parent.top
            anchors.right: parent.right
            anchors.topMargin: 8
            anchors.rightMargin: 12
            width: 76
            height: 24
            radius: 12
            color: cancelMouse.containsMouse ? "#241817" : "#171313"
            border.color: cancelMouse.containsMouse ? theme.danger : theme.frameBorder
            border.width: 1

            Text {
                anchors.centerIn: parent
                text: "Cancel"
                color: cancelMouse.containsMouse ? theme.headline : "#FFAA9A"
                font.family: theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.Bold
            }

            MouseArea {
                id: cancelMouse
                anchors.fill: parent
                hoverEnabled: true
                cursorShape: Qt.PointingHandCursor
                onClicked: controller.cancelDownload()
            }
        }

        Row {
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.top: progressTitle.bottom
            anchors.topMargin: 3
            anchors.leftMargin: 18
            anchors.rightMargin: 18
            height: 14
            spacing: 8

            Text {
                width: parent.width - progressSpeed.width - progressEta.width - parent.spacing * 2
                height: parent.height
                text: root.s.progressAmount || root.s.progressDetails || ""
                color: theme.content
                elide: Text.ElideRight
                font.family: theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.Medium
            }

            Text {
                id: progressSpeed
                width: 76
                height: parent.height
                text: root.s.progressSpeed || ""
                color: theme.content
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideRight
                font.family: theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.Medium
            }

            Text {
                id: progressEta
                width: 86
                height: parent.height
                text: root.s.progressEta || ""
                color: theme.content
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideRight
                font.family: theme.fontFamily
                font.pixelSize: 11
                font.weight: Font.Medium
            }
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

    Item {
        z: 34
        anchors.fill: parent
        visible: root.s.updateNotice && root.s.updateNotice.visible === true

        Rectangle {
            anchors.fill: parent
            color: "#66000000"
        }

        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            anchors.topMargin: 76
            width: Math.min(470, parent.width - 180)
            height: 134
            radius: 18
            color: "#F0111111"
            border.color: theme.frameBorder
            border.width: 1

            Row {
                anchors.fill: parent
                anchors.margins: 18
                spacing: 16

                Rectangle {
                    width: 48
                    height: 48
                    radius: 14
                    color: "#12311F"
                    border.color: "#1F6E3D"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: root.s.updateNotice && root.s.updateNotice.phase === "restarting" ? ">" : "v"
                        color: theme.headline
                        font.family: theme.fontFamily
                        font.pixelSize: 22
                        font.weight: Font.Black
                    }
                }

                Column {
                    width: parent.width - 64
                    spacing: 7

                    Text {
                        width: parent.width
                        text: root.s.updateNotice ? (root.s.updateNotice.title || "Launcher update") : "Launcher update"
                        color: theme.headline
                        elide: Text.ElideRight
                        font.family: theme.fontFamily
                        font.pixelSize: 18
                        font.weight: Font.Black
                    }

                    Text {
                        width: parent.width
                        text: root.s.updateNotice && root.s.updateNotice.version ? "Version " + root.s.updateNotice.version : ""
                        color: "#BDF5D0"
                        elide: Text.ElideRight
                        font.family: theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.Bold
                    }

                    Text {
                        width: parent.width
                        text: root.s.updateNotice ? (root.s.updateNotice.status || "") : ""
                        color: theme.headline
                        elide: Text.ElideRight
                        font.family: theme.fontFamily
                        font.pixelSize: 13
                        font.weight: Font.Bold
                    }

                    Text {
                        width: parent.width
                        text: root.s.updateNotice ? (root.s.updateNotice.details || "") : ""
                        color: theme.content
                        wrapMode: Text.WordWrap
                        font.family: theme.fontFamily
                        font.pixelSize: 11
                        font.weight: Font.Medium
                    }
                }
            }
        }
    }

    Text {
        z: 39
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 18
        anchors.bottomMargin: 8
        width: 90
        height: 16
        text: root.s.version ? "v" + root.s.version : ""
        color: "#90C8D0D4"
        elide: Text.ElideRight
        font.family: theme.fontFamily
        font.pixelSize: 11
        font.weight: Font.DemiBold
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

import QtQuick
import QtQuick.Controls
import "../components"

Item {
    id: root

    property var state: ({})
    property var profile: state.selectedProfile || ({})
    property var server: profile.server || null
    property var serverStatus: profile.server_status || null
    property var news: state.news || []
    property string assetsUrl: state.assetsUrl || ""
    property bool hasProfile: !!state.hasSelectedProfile
    signal navigate(string page)

    Theme { id: theme }

    function value(keys, fallback) {
        for (var i = 0; i < keys.length; i++) {
            var current = root.profile[keys[i]]
            if (current !== undefined && current !== null && current !== "")
                return current
        }
        return fallback
    }

    function hasServer() {
        return root.server !== null && root.server !== undefined
    }

    function asset(name) {
        return assetsUrl !== "" ? assetsUrl + "/Images/" + name : ""
    }

    function serverTitle() {
        if (!root.hasServer())
            return ""
        return root.server.name || root.server.host || "On server"
    }

    function playersText() {
        if (!root.hasServer())
            return ""
        if (!root.serverStatus)
            return "Loading..."
        if (root.serverStatus.online !== true)
            return "Offline"
        var players = root.serverStatus.players || {}
        var online = players.online || 0
        var maxPlayers = players.max || 0
        return maxPlayers > 0 ? online + "/" + maxPlayers + " pl." : online + " pl."
    }

    Item {
        id: content
        anchors.fill: parent
        anchors.leftMargin: 125
        anchors.rightMargin: 25
        anchors.topMargin: 25
        anchors.bottomMargin: 25

        Rectangle {
            id: onlinePanel
            visible: root.hasServer()
            anchors.left: parent.left
            anchors.top: parent.top
            width: 214
            height: 74
            radius: 12
            color: theme.frame
            border.color: theme.frameBorder
            border.width: 1

            Rectangle {
                anchors.left: parent.left
                anchors.leftMargin: 10
                anchors.verticalCenter: parent.verticalCenter
                width: 50
                height: 50
                radius: 8
                color: theme.primary

                SharpImage {
                    anchors.centerIn: parent
                    width: 32
                    height: 32
                    source: root.asset("users.svg")
                }
            }

            Column {
                anchors.left: parent.left
                anchors.leftMargin: 72
                anchors.right: parent.right
                anchors.rightMargin: 12
                anchors.verticalCenter: parent.verticalCenter
                spacing: 3

                Text {
                    width: parent.width
                    text: root.serverTitle()
                    color: theme.content
                    elide: Text.ElideRight
                    font.family: theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.Medium
                }

                Text {
                    width: parent.width
                    text: root.playersText()
                    color: root.serverStatus && root.serverStatus.online === true ? theme.headline : theme.content
                    elide: Text.ElideRight
                    font.family: theme.fontFamily
                    font.pixelSize: 17
                    font.weight: Font.Black
                }
            }
        }

        Column {
            id: serverInfo
            width: Math.max(360, content.width - newsBlock.width - 42)
            anchors.left: parent.left
            anchors.verticalCenter: parent.verticalCenter
            anchors.verticalCenterOffset: 35
            spacing: 20

            Row {
                visible: root.hasProfile
                spacing: 8
                StatusBadge { text: root.state.offlineMode ? "Offline cache" : "Available" }
                StatusBadge { text: root.value(["minecraft_version", "game_version"], "1.21.1") }
                StatusBadge { text: root.state.offlineMode ? "No sync" : root.value(["state", "status"], "Ready") }
                StatusBadge { visible: !!root.profile.opening_mode; text: "Opening" }
            }

            Text {
                width: parent.width
                text: root.hasProfile ? root.value(["name", "display_name"], "BebraLand") : "No packs available"
                color: theme.headline
                wrapMode: Text.WordWrap
                font.family: theme.fontFamily
                font.pixelSize: 60
                font.weight: Font.Black
            }

            Text {
                width: Math.min(parent.width, 500)
                text: root.hasProfile ? (!root.profile.launch_allowed && root.profile.opening_mode ? "Opening Mode: files are available to download. Launch is reserved for launcher admins." : (root.state.offlineMode ? "Backend unavailable. Launch uses already downloaded local pack files." : root.value(["description", "slug"], ""))) : "All packs are disabled or not created yet."
                color: theme.content
                wrapMode: Text.WordWrap
                lineHeight: 1.35
                font.family: theme.fontFamily
                font.pixelSize: 14
                font.weight: Font.Medium
            }

            Row {
                spacing: 10

                Rectangle {
                    id: playSplit
                    width: 156
                    height: 50
                    radius: 25
                    color: !enabled ? theme.formHover : (playMouse.active ? theme.primaryHover : theme.primary)
                    clip: true
                    enabled: root.hasProfile && !root.state.playDisabled
                    opacity: enabled ? 1 : 0.55

                    property bool mainActive: playMouse.active && playMouse.mouseX < 113
                    property bool dropActive: playMouse.active && playMouse.mouseX >= 113

                    function roundedContains(x, y, width, height, radius) {
                        if (x < 0 || y < 0 || x > width || y > height)
                            return false

                        var r = Math.max(0, Math.min(radius, width / 2, height / 2))
                        if (r === 0)
                            return true

                        var cx = Math.max(r, Math.min(x, width - r))
                        var cy = Math.max(r, Math.min(y, height - r))
                        var dx = x - cx
                        var dy = y - cy
                        return dx * dx + dy * dy <= r * r
                    }

                    function containsPoint(point) {
                        return roundedContains(point.x, point.y, width, height, radius)
                    }

                    MouseArea {
                        id: playMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        enabled: playSplit.enabled
                        cursorShape: active ? Qt.PointingHandCursor : Qt.ArrowCursor
                        acceptedButtons: Qt.LeftButton

                        readonly property bool active: containsMouse && playSplit.roundedContains(mouseX, mouseY, playSplit.width, playSplit.height, playSplit.radius)

                        onClicked: (mouse) => {
                            if (!playSplit.roundedContains(mouse.x, mouse.y, playSplit.width, playSplit.height, playSplit.radius))
                                return
                            if (mouse.x >= 113)
                                playMenu.open()
                            else
                                controller.launchSelected()
                        }
                    }

                    Rectangle {
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 112
                        color: "transparent"

                        Row {
                            anchors.centerIn: parent
                            spacing: 10

                            Rectangle {
                                width: 22
                                height: 22
                                radius: 11
                                color: "#30FFFFFF"

                                Text {
                                    anchors.centerIn: parent
                                    text: ">"
                                    color: theme.headline
                                    font.family: theme.fontFamily
                                    font.pixelSize: 15
                                    font.weight: Font.Black
                                }
                            }

                            Text {
                                text: root.profile.opening_mode && !root.profile.launch_allowed ? "Opening" : "Play"
                                color: theme.headline
                                font.family: theme.fontFamily
                                font.pixelSize: 16
                                font.weight: Font.Bold
                            }
                        }
                    }

                    Rectangle {
                        x: 112
                        width: 1
                        height: parent.height
                        color: "#30000000"
                    }

                    Rectangle {
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 43
                        color: "transparent"

                        SharpImage {
                            anchors.centerIn: parent
                            width: 18
                            height: 18
                            source: root.asset("down.svg")
                        }
                    }

                    Popup {
                        id: playMenu
                        x: playSplit.width - width
                        y: playSplit.height + 10
                        width: 180
                        height: 96
                        padding: 8
                        modal: false
                        focus: false
                        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

                        background: Rectangle {
                            color: theme.frame
                            radius: 20
                            border.color: theme.frameBorder
                            border.width: 1
                        }

                        contentItem: Column {
                            spacing: 8

                            GmlButton {
                                width: 164
                                height: 36
                                radius: 18
                                kind: "additional"
                                text: "Reinstall"
                                font.pixelSize: 13
                                onClicked: {
                                    playMenu.close()
                                    controller.reinstallSelected()
                                }
                            }

                            GmlButton {
                                width: 164
                                height: 36
                                radius: 18
                                kind: "danger"
                                text: "Delete"
                                font.pixelSize: 13
                                onClicked: {
                                    playMenu.close()
                                    controller.deleteSelected()
                                }
                            }
                        }
                    }
                }

                GmlButton {
                    width: 136
                    text: "Settings"
                    kind: "secondary"
                    iconSource: root.asset("settings.svg")
                    iconSize: 24
                    font.pixelSize: 16
                    onClicked: root.navigate("settings")
                }

                GmlButton {
                    width: 140
                    text: (root.state.optionalMods || []).length > 0 ? "Mods " + (root.state.optionalMods || []).length : "Mods"
                    kind: "secondary"
                    iconSource: root.asset("document.svg")
                    iconSize: 23
                    font.pixelSize: 16
                    enabled: root.hasProfile
                    onClicked: root.navigate("mods")
                }
            }
        }

        Item {
            id: newsBlock
            width: Math.min(440, Math.max(320, content.width * 0.45))
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.topMargin: 34
            anchors.bottom: websiteButton.top
            anchors.bottomMargin: 18

            Text {
                id: newsHeading
                objectName: "newsHeading"
                text: "News"
                color: theme.headline
                font.family: theme.fontFamily
                font.pixelSize: 22
                font.weight: Font.Bold
            }

            ListView {
                id: newsList
                objectName: "newsList"
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: newsHeading.bottom
                anchors.topMargin: 14
                anchors.bottom: parent.bottom
                clip: true
                spacing: 12
                boundsBehavior: Flickable.StopAtBounds
                interactive: contentHeight > height
                model: root.news

                ScrollBar.vertical: ScrollBar {
                    id: newsScroll
                    policy: ScrollBar.AsNeeded
                    width: 4
                    padding: 0

                    contentItem: Rectangle {
                        implicitWidth: 4
                        radius: 2
                        color: newsScroll.hovered || newsScroll.pressed ? theme.content : theme.formBorderHover
                    }
                }

                delegate: Rectangle {
                    id: newsCard
                    objectName: "newsCard"
                    required property var modelData

                    width: newsList.width - (newsList.contentHeight > newsList.height ? 12 : 0)
                    height: newsContent.implicitHeight + 32
                    radius: 18
                    color: newsMouse.active ? theme.formHover : theme.frame
                    border.width: 1
                    border.color: newsMouse.active ? theme.formBorderHover : theme.frameBorder

                    function roundedContains(x, y, width, height, radius) {
                        if (x < 0 || y < 0 || x > width || y > height)
                            return false

                        var r = Math.max(0, Math.min(radius, width / 2, height / 2))
                        var cx = Math.max(r, Math.min(x, width - r))
                        var cy = Math.max(r, Math.min(y, height - r))
                        var dx = x - cx
                        var dy = y - cy
                        return dx * dx + dy * dy <= r * r
                    }

                    Column {
                        id: newsContent
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.top: parent.top
                        anchors.margins: 16
                        spacing: 6

                        Text {
                            objectName: "newsTitle"
                            width: parent.width
                            text: newsCard.modelData.title || "News"
                            textFormat: Text.PlainText
                            color: theme.headline
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                            font.family: theme.fontFamily
                            font.pixelSize: 18
                            font.weight: Font.Bold
                        }

                        Text {
                            objectName: "newsDescription"
                            width: parent.width
                            visible: text !== ""
                            text: newsCard.modelData.description || ""
                            textFormat: Text.PlainText
                            color: theme.content
                            wrapMode: Text.WordWrap
                            maximumLineCount: 2
                            elide: Text.ElideRight
                            lineHeight: 1.15
                            font.family: theme.fontFamily
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }

                        Text {
                            width: parent.width
                            visible: text !== ""
                            text: newsCard.modelData.date || ""
                            textFormat: Text.PlainText
                            color: theme.content
                            elide: Text.ElideRight
                            font.family: theme.fontFamily
                            font.pixelSize: 11
                            font.weight: Font.Medium
                        }
                    }

                    MouseArea {
                        id: newsMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: active ? Qt.PointingHandCursor : Qt.ArrowCursor

                        readonly property bool active: !!newsCard.modelData.url && containsMouse && newsCard.roundedContains(mouseX, mouseY, newsCard.width, newsCard.height, newsCard.radius)

                        onClicked: (mouse) => {
                            if (newsCard.modelData.url && newsCard.roundedContains(mouse.x, mouse.y, newsCard.width, newsCard.height, newsCard.radius))
                                controller.openUrl(newsCard.modelData.url)
                        }
                    }
                }
            }

            Text {
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: newsList.top
                visible: root.news.length === 0
                text: "No news available"
                color: theme.content
                font.family: theme.fontFamily
                font.pixelSize: 14
            }
        }

        GmlButton {
            id: websiteButton
            objectName: "websiteButton"
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            width: 138
            kind: "additional"
            text: "Website"
            iconSource: root.asset("app.svg")
            iconSize: 22
            onClicked: controller.openUrl(root.state.siteUrl)
        }
    }
}

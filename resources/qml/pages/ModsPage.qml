import QtQuick
import "../components"

Item {
    id: root

    property var state: ({})
    property var mods: state.optionalMods || []
    signal navigate(string page)

    Theme { id: theme }

    BackButton {
        x: 125
        y: 22
        assetsUrl: root.state.assetsUrl
        onClicked: root.navigate("home")
    }

    Item {
        id: body
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        anchors.leftMargin: 125
        anchors.rightMargin: 35
        anchors.topMargin: 135
        anchors.bottomMargin: 40

        FrameCard {
            id: infoCard
            anchors.left: parent.left
            anchors.top: parent.top
            width: 300
            height: 178

            Column {
                anchors.fill: parent
                spacing: 14

                Row {
                    spacing: 10
                    Image {
                        width: 28
                        height: 28
                        source: root.state.assetsUrl + "/Images/folder.svg"
                        fillMode: Image.PreserveAspectFit
                    }
                    Text {
                        text: "Mods"
                        color: theme.headline
                        font.family: theme.fontFamily
                        font.pixelSize: 22
                        font.weight: Font.Black
                    }
                }

                Text {
                    width: parent.width - 38
                    x: 38
                    text: "Optional mods for selected profile."
                    color: theme.content
                    wrapMode: Text.WordWrap
                    lineHeight: 1.35
                    font.family: theme.fontFamily
                    font.pixelSize: 14
                    font.weight: Font.Medium
                }
            }
        }

        Item {
            anchors.left: infoCard.right
            anchors.leftMargin: 20
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            FrameCard {
                visible: root.mods.length === 0
                anchors.left: parent.left
                anchors.right: parent.right
                anchors.top: parent.top
                height: 150

                Row {
                    anchors.fill: parent
                    spacing: 18

                    Image {
                        width: 48
                        height: 48
                        source: root.state.assetsUrl + "/Images/folder.svg"
                        fillMode: Image.PreserveAspectFit
                        opacity: 0.7
                    }

                    Column {
                        width: parent.width - 66
                        spacing: 8

                        Text {
                            text: "Empty"
                            color: theme.headline
                            font.family: theme.fontFamily
                            font.pixelSize: 22
                            font.weight: Font.Black
                        }

                        Text {
                            width: parent.width
                            text: "No optional mods in this profile."
                            color: theme.content
                            wrapMode: Text.WordWrap
                            font.family: theme.fontFamily
                            font.pixelSize: 14
                            font.weight: Font.Medium
                        }
                    }
                }
            }

            Flickable {
                id: flick
                visible: root.mods.length > 0
                anchors.fill: parent
                clip: true
                contentWidth: width
                contentHeight: modsColumn.implicitHeight

                Column {
                    id: modsColumn
                    width: flick.width
                    spacing: 10

                    Repeater {
                        model: root.mods

                        delegate: Rectangle {
                            id: rowCard
                            width: modsColumn.width
                            height: Math.max(86, textColumn.implicitHeight + 40)
                            radius: 20
                            color: theme.frame
                            border.width: 1
                            border.color: theme.frameBorder

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

                            Row {
                                anchors.fill: parent
                                anchors.margins: 20
                                spacing: 18

                                CheckRow {
                                    anchors.verticalCenter: parent.verticalCenter
                                    checked: !!modelData.enabled
                                    text: ""
                                    onToggled: function(checked) {
                                        controller.toggleOptionalMod(modelData.id || "", checked)
                                    }
                                }

                                Column {
                                    id: textColumn
                                    width: parent.width - 58
                                    anchors.verticalCenter: parent.verticalCenter
                                    spacing: 4

                                    Text {
                                        width: parent.width
                                        text: modelData.name || modelData.id || "Mod"
                                        color: theme.headline
                                        elide: Text.ElideRight
                                        font.family: theme.fontFamily
                                        font.pixelSize: 15
                                        font.weight: Font.Bold
                                    }

                                    Text {
                                        width: parent.width
                                        text: modelData.details || ""
                                        color: theme.content
                                        wrapMode: Text.WordWrap
                                        lineHeight: 1.25
                                        font.family: theme.fontFamily
                                        font.pixelSize: 12
                                        font.weight: Font.Medium
                                    }
                                }
                            }

                            MouseArea {
                                id: rowMouse
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: active ? Qt.PointingHandCursor : Qt.ArrowCursor

                                readonly property bool active: containsMouse && rowCard.roundedContains(mouseX, mouseY, rowCard.width, rowCard.height, rowCard.radius)

                                onClicked: (mouse) => {
                                    if (!rowCard.roundedContains(mouse.x, mouse.y, rowCard.width, rowCard.height, rowCard.radius))
                                        return
                                    controller.toggleOptionalMod(modelData.id || "", !modelData.enabled)
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

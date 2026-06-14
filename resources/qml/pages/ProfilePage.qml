import QtQuick
import "../components"

Item {
    id: root

    property var state: ({})
    property string skinUrl: state.skinBodyUrl || ""
    signal navigate(string page)

    Theme { id: theme }

    Image {
        x: 82
        y: 28
        width: 38
        height: 38
        source: root.state.assetsUrl + "/Images/logo.svg"
        fillMode: Image.PreserveAspectFit
    }

    BackButton {
        x: 125
        y: 22
        assetsUrl: root.state.assetsUrl
        onClicked: root.navigate("home")
    }

    Item {
        anchors.fill: parent
        anchors.leftMargin: 125
        anchors.rightMargin: 35
        anchors.topMargin: 118
        anchors.bottomMargin: 38

        FrameCard {
            width: Math.min(700, parent.width)
            height: Math.min(430, parent.height)
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.top: parent.top
            contentPadding: 0

            Item {
                anchors.fill: parent

                Rectangle {
                    id: header
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    height: 92
                    color: "#00000000"

                    Rectangle {
                        anchors.left: parent.left
                        anchors.leftMargin: 28
                        anchors.verticalCenter: parent.verticalCenter
                        width: 54
                        height: 54
                        radius: 27
                        color: theme.primary

                        Image {
                            anchors.centerIn: parent
                            width: 30
                            height: 30
                            source: root.state.assetsUrl + "/Images/profile.svg"
                            fillMode: Image.PreserveAspectFit
                            opacity: 0.9
                        }
                    }

                    Column {
                        anchors.left: parent.left
                        anchors.leftMargin: 98
                        anchors.right: logoMark.left
                        anchors.rightMargin: 20
                        anchors.verticalCenter: parent.verticalCenter
                        spacing: 2

                        Text {
                            width: parent.width
                            text: "Profile"
                            color: theme.content
                            elide: Text.ElideRight
                            font.family: theme.fontFamily
                            font.pixelSize: 12
                            font.weight: Font.Medium
                        }

                        Text {
                            width: parent.width
                            text: root.state.accountName || "Player"
                            color: theme.primary
                            elide: Text.ElideRight
                            font.family: theme.fontFamily
                            font.pixelSize: 25
                            font.weight: Font.Black
                        }
                    }

                    Image {
                        id: logoMark
                        anchors.right: parent.right
                        anchors.rightMargin: 28
                        anchors.verticalCenter: parent.verticalCenter
                        width: 46
                        height: 46
                        source: root.state.assetsUrl + "/Images/logo.svg"
                        fillMode: Image.PreserveAspectFit
                        opacity: 0.9
                    }
                }

                Rectangle {
                    id: stage
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: header.bottom
                    anchors.bottom: actions.top
                    anchors.bottomMargin: 18
                    color: "#0D1110"
                    clip: true

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 88
                        gradient: Gradient {
                            GradientStop { position: 0.00; color: "#00101412" }
                            GradientStop { position: 1.00; color: "#70008C45" }
                        }
                    }

                    Canvas {
                        anchors.fill: parent
                        onPaint: {
                            var ctx = getContext("2d")
                            ctx.clearRect(0, 0, width, height)
                            ctx.strokeStyle = theme.primary
                            ctx.lineWidth = 2
                            ctx.beginPath()
                            ctx.moveTo(0, height - 80)
                            ctx.lineTo(width * 0.18, height - 38)
                            ctx.lineTo(width * 0.82, height - 38)
                            ctx.lineTo(width, height - 80)
                            ctx.stroke()
                        }
                        onWidthChanged: requestPaint()
                        onHeightChanged: requestPaint()
                    }

                    Image {
                        visible: root.skinUrl !== ""
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 26
                        height: Math.min(282, parent.height - 18)
                        source: root.skinUrl
                        fillMode: Image.PreserveAspectFit
                        smooth: false
                        cache: false
                    }

                    Image {
                        visible: root.skinUrl === ""
                        anchors.centerIn: parent
                        width: 118
                        height: 118
                        source: root.state.assetsUrl + "/Images/profile.svg"
                        opacity: 0.34
                        fillMode: Image.PreserveAspectFit
                    }
                }

                Row {
                    id: actions
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 26
                    anchors.leftMargin: 30
                    anchors.rightMargin: 30
                    spacing: 20

                    GmlButton {
                        width: (parent.width - 40) / 3
                        kind: "secondary"
                        text: "Refresh"
                        onClicked: controller.refreshSkin()
                    }

                    GmlButton {
                        width: (parent.width - 40) / 3
                        kind: "primary"
                        text: "Upload skin"
                        onClicked: controller.uploadTexture("skin")
                    }

                    GmlButton {
                        width: (parent.width - 40) / 3
                        kind: "secondary"
                        text: "Upload cape"
                        onClicked: controller.uploadTexture("cape")
                    }
                }
            }
        }
    }
}

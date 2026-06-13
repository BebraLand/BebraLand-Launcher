import QtQuick
import "../components"

Item {
    id: root

    property var state: ({})
    property string skinUrl: state.skinBodyUrl || ""
    signal navigate(string page)

    Theme { id: theme }

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
        anchors.topMargin: 135
        anchors.bottomMargin: 40

        FrameCard {
            width: Math.min(620, parent.width)
            height: Math.min(500, parent.height)
            anchors.left: parent.left
            anchors.top: parent.top
            contentPadding: 0

            Item {
                anchors.fill: parent

                Text {
                    id: userName
                    anchors.top: parent.top
                    anchors.topMargin: 18
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: root.state.accountName || "Player"
                    color: theme.primary
                    font.family: theme.fontFamily
                    font.pixelSize: 24
                    font.weight: Font.Black
                }

                Item {
                    id: stage
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: parent.top
                    anchors.topMargin: 72
                    height: 310
                    clip: true

                    Rectangle {
                        anchors.left: parent.left
                        anchors.right: parent.right
                        anchors.bottom: parent.bottom
                        height: 72
                        gradient: Gradient {
                            GradientStop { position: 0.00; color: "#30101412" }
                            GradientStop { position: 1.00; color: "#66008C45" }
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
                            ctx.moveTo(0, height - 72)
                            ctx.lineTo(90, height - 42)
                            ctx.lineTo(width - 90, height - 42)
                            ctx.lineTo(width, height - 72)
                            ctx.stroke()
                        }
                        onWidthChanged: requestPaint()
                        onHeightChanged: requestPaint()
                    }

                    Image {
                        visible: root.skinUrl !== ""
                        anchors.horizontalCenter: parent.horizontalCenter
                        anchors.top: parent.top
                        anchors.topMargin: 12
                        height: 320
                        source: root.skinUrl
                        fillMode: Image.PreserveAspectFit
                        smooth: false
                        cache: false
                    }

                    Image {
                        visible: root.skinUrl === ""
                        anchors.centerIn: parent
                        width: 112
                        height: 112
                        source: root.state.assetsUrl + "/Images/profile.svg"
                        opacity: 0.45
                        fillMode: Image.PreserveAspectFit
                    }
                }

                Row {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    anchors.bottomMargin: 30
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

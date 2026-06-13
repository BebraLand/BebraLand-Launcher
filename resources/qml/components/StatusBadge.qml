import QtQuick

Rectangle {
    id: root

    property string text: ""

    height: 30
    width: Math.max(72, label.implicitWidth + 24)
    radius: 15
    color: "#18000000"
    border.width: 1
    border.color: "#20FFFFFF"

    Theme { id: theme }

    Text {
        id: label
        anchors.centerIn: parent
        text: root.text
        color: theme.content
        font.family: theme.fontFamily
        font.pixelSize: 14
        font.weight: Font.Medium
    }
}

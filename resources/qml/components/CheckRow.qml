import QtQuick

Item {
    id: root

    property bool checked: false
    property string text: ""
    signal toggled(bool checked)

    width: row.implicitWidth
    height: Math.max(24, row.implicitHeight)

    Theme { id: theme }

    Row {
        id: row
        anchors.verticalCenter: parent.verticalCenter
        spacing: 9

        Rectangle {
            width: 20
            height: 20
            radius: 4
            color: root.checked ? theme.primary : theme.form
            border.width: 1
            border.color: root.checked ? theme.primary : theme.content

            Rectangle {
                visible: root.checked
                anchors.centerIn: parent
                width: 8
                height: 8
                radius: 2
                color: theme.headline
                opacity: 0.9
            }
        }

        Text {
            text: root.text
            color: theme.content
            font.family: theme.fontFamily
            font.pixelSize: 14
            font.weight: Font.DemiBold
            verticalAlignment: Text.AlignVCenter
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.toggled(!root.checked)
    }
}

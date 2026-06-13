import QtQuick

Rectangle {
    id: root

    default property alias content: body.data
    property int contentPadding: 30

    color: theme.frame
    border.color: theme.frameBorder
    border.width: 1
    radius: 20
    clip: true

    Theme { id: theme }

    Item {
        id: body
        anchors.fill: parent
        anchors.margins: root.contentPadding
    }
}

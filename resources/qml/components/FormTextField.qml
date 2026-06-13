import QtQuick
import QtQuick.Controls

TextField {
    id: root

    property int radius: 10

    height: 50
    selectByMouse: true
    focusPolicy: Qt.ClickFocus
    color: theme.content
    placeholderTextColor: "#606060"
    selectionColor: theme.primary
    selectedTextColor: theme.headline
    leftPadding: 16
    rightPadding: 16
    verticalAlignment: TextInput.AlignVCenter
    font.family: theme.fontFamily
    font.pixelSize: 13
    font.weight: Font.DemiBold

    Theme { id: theme }

    background: Rectangle {
        radius: root.radius
        color: root.hovered || root.activeFocus ? theme.formHover : theme.form
        border.width: 1
        border.color: root.activeFocus ? theme.primary : (root.hovered ? theme.formBorderHover : theme.formBorder)
    }
}

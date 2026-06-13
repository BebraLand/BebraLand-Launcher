import QtQuick
import QtQuick.Controls

Button {
    id: root

    property string iconSource: ""
    property int iconSize: 22
    property string kind: "secondary"
    property int radius: 25
    property int gap: 10

    focusPolicy: Qt.NoFocus
    hoverEnabled: true
    padding: 0
    height: 50
    font.family: theme.fontFamily
    font.pixelSize: 14
    font.weight: Font.Bold
    implicitWidth: Math.max(root.text.length > 0 ? 120 : root.height, contentRow.implicitWidth + (root.text.length > 0 ? 36 : 0))

    Theme { id: theme }

    containmentMask: QtObject {
        function contains(point) {
            return root.roundedContains(point.x, point.y, root.width, root.height, root.radius)
        }
    }

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

    function baseColor() {
        if (!root.enabled)
            return theme.formHover
        if (root.kind === "primary")
            return root.hovered ? theme.primaryHover : theme.primary
        if (root.kind === "additional")
            return root.hovered ? theme.formHover : theme.form
        if (root.kind === "danger")
            return theme.danger
        if (root.kind === "ghost")
            return "transparent"
        return root.hovered ? theme.secondaryHover : theme.secondary
    }

    background: Rectangle {
        radius: root.radius
        color: root.baseColor()
        border.width: root.kind === "additional" ? 1 : 0
        border.color: root.hovered ? theme.formBorderHover : theme.formBorder
        opacity: root.enabled ? 1 : 0.55
    }

    contentItem: Item {
        implicitWidth: contentRow.implicitWidth
        implicitHeight: root.height

        Row {
            id: contentRow
            anchors.centerIn: parent
            spacing: root.iconSource !== "" && root.text !== "" ? root.gap : 0

            Image {
                visible: root.iconSource !== ""
                source: root.iconSource
                width: root.iconSize
                height: root.iconSize
                sourceSize.width: root.iconSize
                sourceSize.height: root.iconSize
                fillMode: Image.PreserveAspectFit
                opacity: root.enabled ? 1 : 0.5
            }

            Text {
                visible: root.text !== ""
                text: root.text
                color: theme.headline
                font.family: theme.fontFamily
                font.pixelSize: root.font.pixelSize
                font.weight: root.font.weight
                elide: Text.ElideRight
                verticalAlignment: Text.AlignVCenter
            }
        }
    }
}

import QtQuick

Item {
    id: root

    property var state: ({})
    property string page: "home"
    signal pageRequested(string page)

    width: 100

    Theme { id: theme }

    function profiles() {
        return state.profiles || []
    }

    function iconFor(profile) {
        if (profile && profile.icon_url)
            return profile.icon_url
        return state.assetsUrl + "/Images/logo.svg"
    }

    Image {
        anchors.top: parent.top
        anchors.topMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        width: 38
        height: 38
        source: state.assetsUrl + "/Images/logo.svg"
        fillMode: Image.PreserveAspectFit
    }

    Column {
        anchors.verticalCenter: parent.verticalCenter
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 10

        GmlButton {
            width: 60
            height: 60
            radius: 30
            kind: root.page === "profile" ? "primary" : "secondary"
            iconSource: root.state.assetsUrl + "/Images/profile.svg"
            iconSize: 24
            onClicked: root.pageRequested("profile")
        }

        Rectangle {
            width: 60
            height: Math.min(350, Math.max(60, root.profiles().length * 50 + 10))
            radius: 30
            color: theme.secondary
            clip: true

            Column {
                anchors.centerIn: parent
                spacing: 6

                Repeater {
                    model: root.profiles()

                    delegate: Rectangle {
                        id: profileButton

                        width: 50
                        height: 50
                        radius: 25
                        color: modelData.slug === root.state.selectedSlug ? theme.primary : "transparent"

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

                        Image {
                            anchors.centerIn: parent
                            width: 32
                            height: 32
                            source: root.iconFor(modelData)
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                        }

                        MouseArea {
                            id: profileMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: active ? Qt.PointingHandCursor : Qt.ArrowCursor

                            readonly property bool active: containsMouse && profileButton.roundedContains(mouseX, mouseY, profileButton.width, profileButton.height, profileButton.radius)

                            onClicked: (mouse) => {
                                if (!profileButton.roundedContains(mouse.x, mouse.y, profileButton.width, profileButton.height, profileButton.radius))
                                    return
                                controller.selectProfile(modelData.slug || "")
                                root.pageRequested("home")
                            }
                        }
                    }
                }
            }
        }
    }

    GmlButton {
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 28
        anchors.horizontalCenter: parent.horizontalCenter
        width: 60
        height: 60
        radius: 30
        kind: "secondary"
        iconSource: root.state.assetsUrl + "/Images/logout.svg"
        iconSize: 22
        onClicked: controller.logout()
    }
}

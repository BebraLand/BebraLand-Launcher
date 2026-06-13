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
                        width: 50
                        height: 50
                        radius: 25
                        color: modelData.slug === root.state.selectedSlug ? theme.primary : "transparent"

                        Image {
                            anchors.centerIn: parent
                            width: 32
                            height: 32
                            source: root.iconFor(modelData)
                            fillMode: Image.PreserveAspectFit
                            smooth: true
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: {
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

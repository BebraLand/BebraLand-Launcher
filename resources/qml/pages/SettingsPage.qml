import QtQuick
import QtQuick.Controls
import "../components"

Item {
    id: root

    property var state: ({})
    property var ram: state.ram || ({})
    property int editedRam: ram.value || 2048
    property var windowState: state.window || ({})
    property var logCleanup: state.logCleanup || ({})
    property string assetsUrl: state.assetsUrl || ""
    signal navigate(string page)

    Theme { id: theme }

    onRamChanged: {
        editedRam = ram.value || 2048
    }

    function asInt(text, fallback) {
        var value = parseInt(text)
        return isNaN(value) ? fallback : value
    }

    function asset(name) {
        return assetsUrl !== "" ? assetsUrl + "/Images/" + name : ""
    }

    function roundedRam(value) {
        return controller.roundRam(value)
    }

    function updateRam(value) {
        var rounded = roundedRam(value)
        editedRam = rounded
        controller.setRam(rounded)
    }

    function saveWindow(fullscreen) {
        controller.setWindowSettings(
            fullscreen,
            asInt(widthField.text, windowState.width || 900),
            asInt(heightField.text, windowState.height || 600)
        )
    }

    BackButton {
        x: 125
        y: 22
        assetsUrl: root.assetsUrl
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
        anchors.topMargin: 95
        anchors.bottomMargin: 35

        FrameCard {
            id: ramCard
            width: Math.min(350, Math.max(300, body.width * 0.38))
            height: 300
            anchors.left: parent.left
            anchors.top: parent.top

            Column {
                anchors.fill: parent
                spacing: 14

                Row {
                    spacing: 10
                    SharpImage {
                        width: 28
                        height: 28
                        source: root.asset("ram.svg")
                    }
                    Text {
                        text: "Settings RAM"
                        color: theme.headline
                        font.family: theme.fontFamily
                        font.pixelSize: 22
                        font.weight: Font.Black
                    }
                }

                Text {
                    width: parent.width - 38
                    x: 38
                    text: "Configure the amount of RAM consumed."
                    color: theme.content
                    wrapMode: Text.WordWrap
                    lineHeight: 1.35
                    font.family: theme.fontFamily
                    font.pixelSize: 14
                    font.weight: Font.Medium
                }

                Rectangle { width: parent.width; height: 1; color: theme.formBorder }

                Slider {
                    id: ramSlider
                    width: parent.width
                    height: 48
                    from: root.ram.min || 512
                    to: root.ram.max || 16384
                    stepSize: 256
                    snapMode: Slider.NoSnap
                    live: true
                    focusPolicy: Qt.NoFocus

                    Connections {
                        target: root
                        function onRamChanged() {
                            if (!ramSlider.pressed)
                                ramSlider.value = root.ram.value || 2048
                        }
                    }

                    Component.onCompleted: value = root.editedRam
                    onMoved: root.updateRam(value)
                    onPressedChanged: {
                        if (!pressed) {
                            root.updateRam(value)
                            value = root.editedRam
                        }
                    }

                    background: Rectangle {
                        x: ramSlider.leftPadding
                        y: ramSlider.topPadding + ramSlider.availableHeight / 2 - height / 2
                        width: ramSlider.availableWidth
                        height: 4
                        radius: 2
                        color: theme.content

                        Rectangle {
                            width: ramSlider.visualPosition * parent.width
                            height: parent.height
                            radius: parent.radius
                            color: theme.primary
                        }
                    }

                    handle: Rectangle {
                        x: ramSlider.leftPadding + ramSlider.visualPosition * (ramSlider.availableWidth - width)
                        y: ramSlider.topPadding + ramSlider.availableHeight / 2 - height / 2
                        width: 18
                        height: 18
                        radius: 9
                        color: theme.primary
                    }
                }

                Row {
                    width: parent.width
                    spacing: 18

                    FormTextField {
                        width: 125
                        readOnly: true
                        text: String(root.editedRam) + " MB"
                    }

                    Text {
                        width: parent.width - 143
                        anchors.verticalCenter: parent.verticalCenter
                        text: root.ram.recommended ? "Rec. " + root.ram.recommended + " MB" : (root.ram.hint || "")
                        color: "#6F7F96"
                        elide: Text.ElideRight
                        font.family: theme.fontFamily
                        font.pixelSize: 12
                        font.weight: Font.Medium
                    }
                }
            }
        }

        Column {
            anchors.left: ramCard.right
            anchors.leftMargin: 30
            anchors.right: parent.right
            anchors.top: parent.top
            spacing: 20

            FrameCard {
                width: parent.width
                height: 236
                contentPadding: 18

                Column {
                    anchors.fill: parent
                    spacing: 14

                    Row {
                        spacing: 10
                        SharpImage {
                            width: 28
                            height: 28
                            source: root.asset("window.svg")
                        }
                        Text {
                            text: "Window size"
                            color: theme.headline
                            font.family: theme.fontFamily
                            font.pixelSize: 22
                            font.weight: Font.Black
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: theme.formBorder }

                    CheckRow {
                        id: fullscreenCheck
                        checked: !!root.windowState.fullscreen
                        text: "Full screen"
                        onToggled: function(checked) { root.saveWindow(checked) }
                    }

                    Row {
                        visible: !fullscreenCheck.checked
                        width: parent.width
                        spacing: 28

                        FormTextField {
                            id: widthField
                            width: (parent.width - 58) / 2
                            text: String(root.windowState.width || 900)
                            inputMethodHints: Qt.ImhDigitsOnly
                            validator: IntValidator { bottom: 320; top: 7680 }
                            onEditingFinished: root.saveWindow(fullscreenCheck.checked)
                        }

                        Text {
                            text: "x"
                            color: theme.content
                            anchors.verticalCenter: parent.verticalCenter
                            font.family: theme.fontFamily
                            font.pixelSize: 14
                            font.weight: Font.DemiBold
                        }

                        FormTextField {
                            id: heightField
                            width: (parent.width - 58) / 2
                            text: String(root.windowState.height || 600)
                            inputMethodHints: Qt.ImhDigitsOnly
                            validator: IntValidator { bottom: 240; top: 4320 }
                            onEditingFinished: root.saveWindow(fullscreenCheck.checked)
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: theme.formBorder }

                    CheckRow {
                        checked: !!root.state.debugConsole
                        text: "Show Minecraft console"
                        onToggled: function(checked) { controller.setDebugConsole(checked) }
                    }
                }
            }

            FrameCard {
                width: parent.width
                height: 214
                contentPadding: 18

                Column {
                    anchors.fill: parent
                    spacing: 12

                    Row {
                        spacing: 10
                        SharpImage {
                            width: 28
                            height: 28
                            source: root.asset("folder.svg")
                        }
                        Text {
                            text: "Install folder"
                            color: theme.headline
                            font.family: theme.fontFamily
                            font.pixelSize: 22
                            font.weight: Font.Black
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: theme.formBorder }

                    Row {
                        width: parent.width
                        spacing: 14

                        Rectangle {
                            width: parent.width - 136
                            height: 50
                            radius: 10
                            color: theme.form
                            border.width: 1
                            border.color: theme.formBorder

                            Text {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: 16
                                anchors.rightMargin: 16
                                text: root.state.installDir || ""
                                color: theme.content
                                elide: Text.ElideMiddle
                                font.family: theme.fontFamily
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                            }
                        }

                        GmlButton {
                            width: 54
                            height: 50
                            radius: 25
                            kind: "additional"
                            iconSource: root.asset("folder.svg")
                            iconSize: 22
                            onClicked: controller.openInstallFolder()
                        }

                        GmlButton {
                            width: 54
                            height: 50
                            radius: 25
                            kind: "additional"
                            iconSource: root.asset("edit.svg")
                            iconSize: 22
                            onClicked: controller.chooseInstallFolder()
                        }
                    }

                    Rectangle { width: parent.width; height: 1; color: theme.formBorder }

                    Row {
                        width: parent.width
                        height: 50
                        spacing: 14

                        Rectangle {
                            width: parent.width - 198
                            height: 50
                            radius: 10
                            color: theme.form
                            border.width: 1
                            border.color: theme.formBorder

                            Text {
                                anchors.left: parent.left
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                anchors.leftMargin: 16
                                anchors.rightMargin: 16
                                text: "Logs " + (root.logCleanup.sizeText || "0 B")
                                color: theme.content
                                elide: Text.ElideRight
                                font.family: theme.fontFamily
                                font.pixelSize: 13
                                font.weight: Font.DemiBold
                            }
                        }

                        GmlButton {
                            width: 54
                            height: 50
                            radius: 25
                            kind: "additional"
                            iconSource: root.asset("refresh.svg")
                            iconSize: 20
                            onClicked: controller.refreshLogSize()
                        }

                        GmlButton {
                            width: 116
                            height: 50
                            radius: 25
                            kind: "danger"
                            text: "Delete"
                            enabled: !!root.logCleanup.hasLogs
                            onClicked: controller.clearSelectedLogs()
                        }
                    }
                }
            }

        }
    }
}

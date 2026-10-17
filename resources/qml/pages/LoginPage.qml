import QtQuick
import "../components"

Item {
    id: root

    property var state: ({})
    property string assetsUrl: state.assetsUrl || ""

    Theme { id: theme }

    function asset(name) {
        return assetsUrl !== "" ? assetsUrl + "/Images/" + name : ""
    }

    FrameCard {
        width: 380
        height: 455
        anchors.centerIn: parent
        contentPadding: 30

        Column {
            anchors.fill: parent
            spacing: 20

            SharpImage {
                width: 96
                height: 72
                anchors.horizontalCenter: parent.horizontalCenter
                source: root.asset("logo.svg")
            }

            Rectangle {
                width: parent.width
                height: 1
                color: theme.formBorder
            }

            Column {
                width: parent.width
                spacing: 8

                Text {
                    text: "Login"
                    color: theme.content
                    font.family: theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }

                FormTextField {
                    id: loginField
                    width: parent.width
                    placeholderText: "email or username"
                    Keys.onReturnPressed: controller.login(loginField.text, passwordField.text, "")
                }
            }

            Column {
                width: parent.width
                spacing: 8

                Text {
                    text: "Password"
                    color: theme.content
                    font.family: theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }

                FormTextField {
                    id: passwordField
                    width: parent.width
                    echoMode: TextInput.Password
                    placeholderText: "password"
                    Keys.onReturnPressed: controller.login(loginField.text, passwordField.text, "")
                }
            }

            Text {
                width: parent.width
                height: Math.max(18, implicitHeight)
                text: root.state.loginStatus || ""
                color: root.state.loginError ? theme.danger : theme.content
                wrapMode: Text.WordWrap
                font.family: theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }

            GmlButton {
                width: parent.width
                kind: "primary"
                enabled: !root.state.loginBusy
                text: "Login to BebraLand"
                iconSource: root.asset("login.svg")
                iconSize: 24
                onClicked: controller.login(loginField.text, passwordField.text, "")
            }

            Item {
                width: parent.width
                height: 5
            }
        }
    }

    Rectangle {
        visible: root.state.twoFactorVisible
        anchors.fill: parent
        color: "#B0000000"
        z: 50

        FrameCard {
            width: 350
            height: 300
            anchors.centerIn: parent
            contentPadding: 30

            Column {
                anchors.fill: parent
                spacing: 18

                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    text: "Two-factor code"
                    color: theme.headline
                    font.family: theme.fontFamily
                    font.pixelSize: 20
                    font.weight: Font.Bold
                }

                Text {
                    width: parent.width
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    text: root.state.loginError ? root.state.loginStatus : "Enter 2FA code from your Azuriom account."
                    color: root.state.loginError ? theme.danger : theme.content
                    lineHeight: 1.35
                    font.family: theme.fontFamily
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                }

                FormTextField {
                    id: codeField
                    width: parent.width
                    maximumLength: 8
                    horizontalAlignment: TextInput.AlignHCenter
                    placeholderText: "2FA"
                    font.pixelSize: 22
                    font.weight: Font.Bold
                    Keys.onReturnPressed: controller.confirm2fa(codeField.text)
                }

                GmlButton {
                    width: parent.width
                    kind: "additional"
                    enabled: !root.state.loginBusy
                    text: "Confirm"
                    iconSource: root.asset("password.svg")
                    iconSize: 22
                    onClicked: controller.confirm2fa(codeField.text)
                }
            }
        }
    }
}

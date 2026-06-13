import QtQuick
import "../components"

Item {
    id: root

    property var state: ({})

    Theme { id: theme }

    FrameCard {
        width: 380
        height: 430
        anchors.centerIn: parent
        contentPadding: 30

        Column {
            anchors.fill: parent
            spacing: 20

            Image {
                width: 96
                height: 72
                anchors.horizontalCenter: parent.horizontalCenter
                source: root.state.assetsUrl + "/Images/logo.svg"
                fillMode: Image.PreserveAspectFit
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
                height: 18
                text: root.state.loginStatus || ""
                color: text.toLowerCase().indexOf("error") >= 0 ? theme.danger : theme.content
                elide: Text.ElideRight
                font.family: theme.fontFamily
                font.pixelSize: 12
                font.weight: Font.DemiBold
            }

            GmlButton {
                width: parent.width
                kind: "primary"
                text: "Login Azuriom"
                iconSource: root.state.assetsUrl + "/Images/login.svg"
                iconSize: 24
                onClicked: controller.login(loginField.text, passwordField.text, "")
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
                    text: "Enter 2FA code from your Azuriom account."
                    color: theme.content
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
                    text: "Confirm"
                    iconSource: root.state.assetsUrl + "/Images/password.svg"
                    iconSize: 22
                    onClicked: controller.confirm2fa(codeField.text)
                }
            }
        }
    }
}

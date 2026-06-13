import QtQuick

GmlButton {
    property string assetsUrl: ""

    width: 112
    height: 50
    radius: 25
    kind: "additional"
    text: "Back"
    iconSource: assetsUrl + "/Images/back.svg"
    iconSize: 22
}

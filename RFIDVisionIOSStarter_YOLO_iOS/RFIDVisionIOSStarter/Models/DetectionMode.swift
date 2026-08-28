import Foundation

enum DetectionMode: String, CaseIterable, Identifiable, Codable {
    case yolo = "YOLO"
    case aruco = "ArUco"

    var id: String { rawValue }

    var apiValue: String {
        switch self {
        case .yolo: return "yolo"
        case .aruco: return "aruco"
        }
    }

    var descriptionText: String {
        switch self {
        case .yolo:
            return "YOLO 객체 인식 모드입니다. 기기 내 추론 또는 서버 추론 중 하나를 선택할 수 있습니다."
        case .aruco:
            return "ArUco 마커 인식 자리입니다. OpenCV aruco 연결 전까지는 placeholder로 유지됩니다."
        }
    }
}

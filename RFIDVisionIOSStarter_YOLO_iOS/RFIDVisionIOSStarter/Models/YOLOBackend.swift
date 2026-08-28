import Foundation

enum YOLOBackend: String, CaseIterable, Identifiable, Codable {
    case onDevice = "On-Device"
    case server = "Server"

    var id: String { rawValue }

    var apiValue: String {
        switch self {
        case .onDevice: return "on_device"
        case .server: return "server"
        }
    }

    var descriptionText: String {
        switch self {
        case .onDevice:
            return "Core ML + Vision으로 아이폰 내부에서 YOLO 추론"
        case .server:
            return "프레임 이미지를 FastAPI 서버로 전송하고 서버에서 YOLO 추론"
        }
    }
}

import Foundation

struct Box: Codable {
    let x: Double
    let y: Double
    let width: Double
    let height: Double
    let label: String
    let confidence: Double
}

struct DetectionResult: Codable, Identifiable {
    let id = UUID()
    let mode: String
    let label: String
    let confidence: Double?
    let payload: [String: String]
    let createdAt: String
    
    let boxes: [Box]?
}

struct ServerInferenceResponse: Codable {
    let label: String
    let confidence: Double?
    let payload: [String: String]?
    let boxes: [Box]?
}

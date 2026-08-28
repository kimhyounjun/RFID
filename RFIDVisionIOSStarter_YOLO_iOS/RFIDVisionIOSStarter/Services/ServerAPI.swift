import Foundation
import UIKit

final class ServerAPI {
    static let shared = ServerAPI()
    private init() {}

    // 🔥 여기서 서버 URL 고정
    private let serverURL = "https://goniometrically-confarreated-shavon.ngrok-free.dev/vision/yolo"

    func uploadFrame(
        image: UIImage,
        mode: DetectionMode,
        metadata: [String: String]
    ) async throws {
        _ = try await performMultipartRequest(
            image: image,
            mode: mode,
            metadata: metadata
        )
    }

    func inferYOLO(
        image: UIImage,
        metadata: [String: String]
    ) async throws -> DetectionResult {
        let data = try await performMultipartRequest(
            image: image,
            mode: .yolo,
            metadata: metadata
        )

        let decoder = JSONDecoder()
        if let decoded = try? decoder.decode(ServerInferenceResponse.self, from: data) {
            return DetectionResult(
                mode: "yolo_server",
                label: decoded.label,
                confidence: decoded.confidence,
                payload: decoded.payload ?? [:],
                createdAt: ISO8601DateFormatter().string(from: Date()),
                boxes: decoded.boxes // 🔥 핵심
            )
        }

        if let rawText = String(data: data, encoding: .utf8), !rawText.isEmpty {
            return DetectionResult(
                mode: "yolo_server",
                label: "server_response",
                confidence: nil,
                payload: ["raw": rawText],
                createdAt: ISO8601DateFormatter().string(from: Date()),
                boxes: nil
            )
        }

        return DetectionResult(
            mode: "yolo_server",
            label: "ok",
            confidence: nil,
            payload: [:],
            createdAt: ISO8601DateFormatter().string(from: Date()),
            boxes: nil
        )
    }

    private func performMultipartRequest(
        image: UIImage,
        mode: DetectionMode,
        metadata: [String: String]
    ) async throws -> Data {
        guard let url = URL(string: serverURL) else {
            throw URLError(.badURL)
        }

        guard let imageData = image.jpegData(compressionQuality: 0.7) else {
            throw URLError(.cannotParseResponse)
        }

        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.timeoutInterval = 30
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json, text/plain, */*", forHTTPHeaderField: "Accept")

        let jsonData = try JSONSerialization.data(withJSONObject: metadata, options: [])
        let jsonString = String(data: jsonData, encoding: .utf8) ?? "{}"

        var body = Data()
        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"mode\"\r\n\r\n")
        body.appendString("\(mode.apiValue)\r\n")

        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"timestamp\"\r\n\r\n")
        body.appendString("\(ISO8601DateFormatter().string(from: Date()))\r\n")

        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"metadata\"\r\n\r\n")
        body.appendString("\(jsonString)\r\n")

        body.appendString("--\(boundary)\r\n")
        body.appendString("Content-Disposition: form-data; name=\"image\"; filename=\"frame.jpg\"\r\n")
        body.appendString("Content-Type: image/jpeg\r\n\r\n")
        body.append(imageData)
        body.appendString("\r\n")

        body.appendString("--\(boundary)--\r\n")
        request.httpBody = body

        let (data, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            let responseText = String(data: data, encoding: .utf8) ?? ""
            throw NSError(
                domain: "ServerAPI",
                code: (response as? HTTPURLResponse)?.statusCode ?? -1,
                userInfo: [NSLocalizedDescriptionKey: "서버 응답 오류 \(responseText)"]
            )
        }

        return data
    }
}

private extension Data {
    mutating func appendString(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}

import AVFoundation
import UIKit

final class ArucoDetector: FrameDetector {
    func detect(from sampleBuffer: CMSampleBuffer) -> DetectionResult? {
        guard let image = SampleBufferConverter.image(from: sampleBuffer),
              let cgImage = image.cgImage else {
            return nil
        }

        // 🔥 placeholder (OpenCV 대신)
        let detectedIds: [Int] = []

        let label = detectedIds.isEmpty ? "aruco_placeholder" : "marker_detected"
        let payload = [
            "ids": detectedIds.map(String.init).joined(separator: ","),
            "message": detectedIds.isEmpty
                ? "OpenCV aruco 연동 전 placeholder 상태입니다."
                : "marker ids detected"
        ]

        return DetectionResult(
            mode: "aruco",
            label: label,
            confidence: nil,
            payload: payload,
            createdAt: ISO8601DateFormatter().string(from: Date()),
            boxes: nil // ✅ 이거 추가
        )
    }

    func previewImage(from sampleBuffer: CMSampleBuffer) -> UIImage? {
        SampleBufferConverter.image(from: sampleBuffer)
    }
}

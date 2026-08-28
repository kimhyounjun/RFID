import AVFoundation
import Combine
import Foundation
import UIKit

@MainActor
final class CameraViewModel: ObservableObject {

    @Published var selectedMode: DetectionMode = .yolo
    @Published var yoloBackend: YOLOBackend = .onDevice
    @Published var isStreaming = false
    @Published var latestStatus: String = "대기 중"
    @Published var latestResultText: String = "결과 없음"

    // 🔥 BoundingBox → Box로 변경
    @Published var boundingBoxes: [Box] = []

    @Published var confidenceThreshold: Float = 0.35
    @Published var processInterval: Double = 0.20
    @Published var detectedCount: Int = 0
    @Published var modelStatusText: String = "모델 확인 중..."

    let cameraManager = CameraManager()

    private lazy var yoloDetector = YOLODetector()
    private lazy var arucoDetector = ArucoDetector()

    private var frameThrottleDate = Date.distantPast

    init() {
        modelStatusText = yoloDetector.modelStatusText

        cameraManager.onFrame = { [weak self] sampleBuffer in
            Task { @MainActor in
                self?.handleFrame(sampleBuffer)
            }
        }
    }

    func setupCamera() {
        cameraManager.requestPermissionAndConfigure()
        refreshModelStatus()
    }

    func refreshModelStatus() {
        modelStatusText = yoloDetector.modelStatusText
    }

    func startStreaming() {
        refreshModelStatus()
        isStreaming = true
        latestStatus = selectedMode == .yolo ? "카메라 시작" : "ArUco 준비 중"
        cameraManager.start()
    }

    func stopStreaming() {
        isStreaming = false
        latestStatus = "카메라 정지"
        latestResultText = "결과 없음"
        detectedCount = 0
        boundingBoxes = []
        cameraManager.stop()
    }

    private func handleFrame(_ sampleBuffer: CMSampleBuffer) {
        guard Date().timeIntervalSince(frameThrottleDate) >= processInterval else { return }
        frameThrottleDate = Date()

        switch selectedMode {
        case .yolo:
            handleYOLO(sampleBuffer)
        case .aruco:
            handleAruco(sampleBuffer)
        }
    }

    private func handleYOLO(_ sampleBuffer: CMSampleBuffer) {

        switch yoloBackend {

        case .onDevice:

            // 🔥 minimumConfidence 제거됨
            if let result = yoloDetector.detect(from: sampleBuffer) {

                latestStatus = result.label == "model_not_found"
                    ? "온디바이스 모델 없음"
                    : "YOLO 추론 완료"

                latestResultText = format(result)

                // 🔥 convert 제거 → 바로 사용
                boundingBoxes = result.boxes ?? []

                detectedCount = boundingBoxes.count

                modelStatusText = yoloDetector.modelStatusText
            }

        case .server:

            guard let image = yoloDetector.previewImage(from: sampleBuffer) else { return }

            latestStatus = "YOLO 서버 요청 중..."

            let metadata = commonMetadata(extra: [
                "backend": yoloBackend.apiValue,
                "mode": selectedMode.apiValue,
                "confidence_threshold": String(format: "%.2f", confidenceThreshold)
            ])

            Task {
                do {
                    let result = try await ServerAPI.shared.inferYOLO(
                        image: image,
                        metadata: metadata
                    )

                    await MainActor.run {
                        self.latestStatus = "YOLO 서버 완료"
                        self.latestResultText = self.format(result)

                        // 🔥 서버도 동일하게 Box 사용
                        self.boundingBoxes = result.boxes ?? []

                        self.detectedCount = self.boundingBoxes.count
                    }
                } catch {
                    await MainActor.run {
                        self.latestStatus = "서버 실패: \(error.localizedDescription)"
                    }
                }
            }
        }
    }

    private func handleAruco(_ sampleBuffer: CMSampleBuffer) {
        if let result = arucoDetector.detect(from: sampleBuffer) {
            latestStatus = "ArUco 실행 중"
            latestResultText = format(result)
            detectedCount = 0
            boundingBoxes = []
        }
    }

    private func commonMetadata(extra: [String: String] = [:]) -> [String: String] {
        var base: [String: String] = [
            "device": UIDevice.current.model,
            "os": UIDevice.current.systemVersion,
            "app_mode": selectedMode.apiValue
        ]
        extra.forEach { base[$0.key] = $0.value }
        return base
    }

    private func format(_ result: DetectionResult) -> String {
        let confidenceText: String
        if let confidence = result.confidence {
            confidenceText = String(format: "%.2f", confidence)
        } else {
            confidenceText = "-"
        }

        if let message = result.payload["message"], !message.isEmpty {
            return "[\(result.mode)] \(result.label) | \(message)"
        }

        if let count = result.payload["count"] {
            return "[\(result.mode)] \(result.label) | conf: \(confidenceText) | count: \(count)"
        }

        return "[\(result.mode)] \(result.label) | conf: \(confidenceText)"
    }
}

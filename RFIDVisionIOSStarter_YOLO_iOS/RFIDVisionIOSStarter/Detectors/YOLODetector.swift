import AVFoundation
import Vision
import CoreML
import UIKit

final class YOLODetector: FrameDetector {

    // MARK: - Model
    private lazy var cachedVisionModel: VNCoreMLModel? = loadVisionModel()

    // MARK: - Status
    var modelStatusText: String {
        if cachedVisionModel != nil {
            return "온디바이스 모델 로드 완료"
        } else {
            return "YOLO 모델 없음"
        }
    }

    // MARK: - Detection
    func detect(from sampleBuffer: CMSampleBuffer) -> DetectionResult? {

        guard let pixelBuffer = CMSampleBufferGetImageBuffer(sampleBuffer) else {
            return nil
        }

        // 모델 없음
        guard let visionModel = cachedVisionModel else {
            return DetectionResult(
                mode: "yolo_on_device",
                label: "model_not_found",
                confidence: nil,
                payload: ["message": "모델 없음"],
                createdAt: ISO8601DateFormatter().string(from: Date()),
                boxes: []
            )
        }

        // 요청 생성
        let request = VNCoreMLRequest(model: visionModel)
        request.imageCropAndScaleOption = .scaleFill

        // 핸들러
        let handler = VNImageRequestHandler(
            cvPixelBuffer: pixelBuffer,
            orientation: .up,
            options: [:]
        )

        // 실행
        do {
            try handler.perform([request])
        } catch {
            return DetectionResult(
                mode: "yolo_on_device",
                label: "inference_failed",
                confidence: nil,
                payload: ["message": "추론 실패"],
                createdAt: ISO8601DateFormatter().string(from: Date()),
                boxes: []
            )
        }

        // 결과 처리
        if let observations = request.results as? [VNRecognizedObjectObservation] {

            let boxes: [Box] = observations.compactMap { obs in
                guard let top = obs.labels.first,
                      top.confidence > 0.4 else { return nil }

                return Box(
                    x: Double(obs.boundingBox.origin.x),
                    y: Double(1 - obs.boundingBox.origin.y - obs.boundingBox.size.height), // 좌표 보정
                    width: Double(obs.boundingBox.size.width),
                    height: Double(obs.boundingBox.size.height),
                    label: top.identifier,
                    confidence: Double(top.confidence)
                )
            }

            return DetectionResult(
                mode: "yolo_on_device",
                label: boxes.first?.label ?? "no_object",
                confidence: boxes.first?.confidence,
                payload: [:],
                createdAt: ISO8601DateFormatter().string(from: Date()),
                boxes: boxes
            )
        }

        // 객체 없음
        return DetectionResult(
            mode: "yolo_on_device",
            label: "no_object",
            confidence: nil,
            payload: [:],
            createdAt: ISO8601DateFormatter().string(from: Date()),
            boxes: []
        )
    }

    // MARK: - Preview
    func previewImage(from sampleBuffer: CMSampleBuffer) -> UIImage? {
        return SampleBufferConverter.image(from: sampleBuffer)
    }

    // MARK: - Model Load
    private func loadVisionModel() -> VNCoreMLModel? {

        guard let modelURL = Bundle.main.url(forResource: "YOLOv8n", withExtension: "mlmodelc") else {
            print("❌ YOLO 모델 파일 없음 (mlmodelc)")
            return nil
        }

        do {
            let model = try MLModel(contentsOf: modelURL)
            return try VNCoreMLModel(for: model)
        } catch {
            print("❌ 모델 로드 실패:", error)
            return nil
        }
    }
}

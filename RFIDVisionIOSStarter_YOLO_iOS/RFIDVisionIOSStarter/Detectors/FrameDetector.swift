import AVFoundation
import UIKit

protocol FrameDetector {
    func detect(from sampleBuffer: CMSampleBuffer) -> DetectionResult?
    func previewImage(from sampleBuffer: CMSampleBuffer) -> UIImage?
}

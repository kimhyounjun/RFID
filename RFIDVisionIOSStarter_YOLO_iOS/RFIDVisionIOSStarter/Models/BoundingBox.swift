import Foundation
import CoreGraphics

struct BoundingBox: Identifiable {
    let id = UUID()
    let rect: CGRect
    let label: String
    let confidence: Float
}

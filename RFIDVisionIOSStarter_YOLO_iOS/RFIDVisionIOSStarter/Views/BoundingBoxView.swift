import SwiftUI

struct BoundingBoxView: View {
    let box: BoundingBox
    let geometry: GeometryProxy

    var body: some View {
        let rect = CGRect(
            x: box.rect.origin.x * geometry.size.width,
            y: box.rect.origin.y * geometry.size.height,
            width: box.rect.width * geometry.size.width,
            height: box.rect.height * geometry.size.height
        )

        ZStack(alignment: .topLeading) {
            Rectangle()
                .stroke(Color.red, lineWidth: 2)
                .frame(width: rect.width, height: rect.height)
                .position(x: rect.midX, y: rect.midY)

            Text("\(box.label) \(String(format: "%.2f", box.confidence))")
                .font(.caption2)
                .padding(4)
                .background(Color.black.opacity(0.6))
                .foregroundColor(.white)
                .position(x: rect.minX + 40, y: rect.minY + 10)
        }
    }
}

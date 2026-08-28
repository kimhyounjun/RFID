import SwiftUI

struct BoundingBoxOverlayView: View {

    let boxes: [Box]

    var body: some View {
        GeometryReader { geo in
            ForEach(boxes.indices, id: \.self) { i in
                let box = boxes[i]

                let rect = CGRect(
                    x: box.x * geo.size.width,
                    y: box.y * geo.size.height,
                    width: box.width * geo.size.width,
                    height: box.height * geo.size.height
                )

                ZStack(alignment: .topLeading) {

                    Rectangle()
                        .stroke(Color.red, lineWidth: 2)
                        .frame(width: rect.width, height: rect.height)
                        .position(
                            x: rect.midX,
                            y: rect.midY
                        )

                    Text("\(box.label) \(String(format: "%.2f", box.confidence))")
                        .font(.caption2)
                        .padding(4)
                        .background(Color.red.opacity(0.7))
                        .foregroundColor(.white)
                        .offset(x: rect.minX, y: rect.minY - 20)
                }
            }
        }
        .allowsHitTesting(false)
    }
}

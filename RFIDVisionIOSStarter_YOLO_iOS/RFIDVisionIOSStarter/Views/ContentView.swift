import SwiftUI

struct ContentView: View {
    @StateObject private var viewModel = CameraViewModel()
    @State private var isCameraMode = false
    @State private var showArucoAlert = false

    var body: some View {
        NavigationStack {
            Group {
                if isCameraMode {
                    cameraView
                } else {
                    startView
                }
            }
            .navigationTitle(isCameraMode ? "실시간 감지" : "RFID Vision")
        }
        .onDisappear {
            viewModel.stopStreaming()
        }
    }
}

extension ContentView {

    var startView: some View {
        GeometryReader { geometry in
            let isWide = geometry.size.width > 900

            ScrollView {
                Group {
                    if isWide {
                        HStack(alignment: .top, spacing: 20) {
                            setupCard
                            infoCard
                        }
                    } else {
                        VStack(spacing: 20) {
                            setupCard
                            infoCard
                        }
                    }
                }
                .padding()
            }
        }
        .onAppear {
            viewModel.setupCamera()
        }
    }

    private var setupCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            Text("온디바이스 YOLO 설정")
                .font(.title2.bold())

            Picker("인식 모드", selection: $viewModel.selectedMode) {
                ForEach(DetectionMode.allCases) { mode in
                    Text(mode.rawValue).tag(mode)
                }
            }
            .pickerStyle(.segmented)

            Text(viewModel.selectedMode.descriptionText)
                .font(.footnote)
                .foregroundStyle(.secondary)

            if viewModel.selectedMode == .yolo {
                VStack(alignment: .leading, spacing: 12) {
                    Picker("YOLO 방식", selection: $viewModel.yoloBackend) {
                        ForEach(YOLOBackend.allCases) { backend in
                            Text(backend.rawValue).tag(backend)
                        }
                    }
                    .pickerStyle(.segmented)

                    Text(viewModel.yoloBackend.descriptionText)
                        .font(.footnote)
                        .foregroundStyle(.secondary)

                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("신뢰도 임계값")
                            Spacer()
                            Text(String(format: "%.2f", viewModel.confidenceThreshold))
                                .foregroundStyle(.secondary)
                        }

                        Slider(value: $viewModel.confidenceThreshold, in: 0.1...0.9, step: 0.05)
                    }

                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("프레임 처리 간격")
                            Spacer()
                            Text(String(format: "%.2f초", viewModel.processInterval))
                                .foregroundStyle(.secondary)
                        }

                        Slider(value: $viewModel.processInterval, in: 0.1...1.0, step: 0.05)
                    }
                }
            }

            Button {
                if viewModel.selectedMode == .aruco {
                    showArucoAlert = true
                    return
                }

                viewModel.startStreaming()
                isCameraMode = true
            } label: {
                Label("시작", systemImage: "play.fill")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
        }
        .padding(20)
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .alert("준비중입니다", isPresented: $showArucoAlert) {
            Button("확인", role: .cancel) {}
        } message: {
            Text("현재 zip은 YOLO 온디바이스 흐름에 맞춰 정리되어 있고, ArUco는 다음 단계에서 붙이면 됩니다.")
        }
    }

    private var infoCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("체크 포인트")
                .font(.title3.bold())

            statusRow(title: "카메라 상태", value: viewModel.cameraManager.permissionDenied ? "권한 필요" : "준비 가능")
            statusRow(title: "모델 상태", value: viewModel.modelStatusText)
            statusRow(title: "권장 디바이스", value: "iPad / iPhone 모두 가능")
            statusRow(title: "현재 기본값", value: "On-Device")

            Divider()

            Text("모델 파일명")
                .font(.headline)
            Text("YOLOv8n.mlpackage 또는 YOLOv8n.mlmodel")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            Text("Resources/Models 폴더에 넣고 Xcode target membership 체크하면 바로 온디바이스 추론 흐름으로 연결됩니다.")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding(20)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.thinMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 20))
    }

    private func statusRow(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.subheadline.weight(.semibold))
            Text(value)
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
    }
}

extension ContentView {

    var cameraView: some View {
        ZStack {
            CameraPreviewView(session: viewModel.cameraManager.session)
                .ignoresSafeArea()

            BoundingBoxOverlayView(boxes: viewModel.boundingBoxes)

            VStack(spacing: 12) {
                HStack {
                    infoBadge(title: "백엔드", value: viewModel.yoloBackend.rawValue)
                    infoBadge(title: "감지 수", value: "\(viewModel.detectedCount)")
                    Spacer()
                }
                .padding(.horizontal)
                .padding(.top, 12)

                Spacer()

                VStack(alignment: .leading, spacing: 10) {
                    Text(viewModel.latestStatus)
                        .font(.headline)
                        .foregroundStyle(.white)

                    Text(viewModel.latestResultText)
                        .font(.footnote)
                        .foregroundStyle(.white.opacity(0.92))

                    HStack {
                        Button {
                            viewModel.stopStreaming()
                            isCameraMode = false
                        } label: {
                            Label("중지", systemImage: "stop.fill")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.borderedProminent)

                        Button {
                            viewModel.refreshModelStatus()
                        } label: {
                            Label("모델 상태", systemImage: "arrow.clockwise")
                                .frame(maxWidth: .infinity)
                        }
                        .buttonStyle(.bordered)
                        .tint(.white)
                    }
                }
                .padding()
                .background(.black.opacity(0.45))
                .clipShape(RoundedRectangle(cornerRadius: 18))
                .padding()
            }
        }
    }

    private func infoBadge(title: String, value: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(.white.opacity(0.75))
            Text(value)
                .font(.caption.bold())
                .foregroundStyle(.white)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.black.opacity(0.4))
        .clipShape(Capsule())
    }
}

# On-Device YOLO 모델 추가 가이드

이 프로젝트는 iPad/iPhone에서 **Core ML + Vision 기반 온디바이스 YOLO 추론**을 할 수 있게 정리되어 있습니다.

## 1. Ultralytics에서 Core ML로 내보내기

```bash
pip install ultralytics coremltools
```

```bash
yolo export model=best.pt format=coreml imgsz=640 nms=True
```

생성 결과 예시:
- `best.mlpackage`

## 2. 파일명 변경

앱 코드에서 기본적으로 찾는 이름은 아래 둘 중 하나입니다.
- `YOLOv8n.mlpackage`
- `YOLOv8n.mlmodel`

그래서 `best.mlpackage`를 `YOLOv8n.mlpackage`로 바꾸면 바로 연결하기 편합니다.

## 3. Xcode에 추가

- `RFIDVisionIOSStarter/Resources/Models` 폴더에 넣기
- Xcode에서 **Target Membership = RFIDVisionIOSStarter** 체크

## 4. 실행 확인

시작 화면의 **모델 상태**가 아래처럼 나오면 연결 성공입니다.
- `온디바이스 모델 로드 완료`

## 5. 현재 zip에 들어간 변경점

- iPad 대응 레이아웃 추가
- YOLO 기본값을 `On-Device`로 변경
- 신뢰도 임계값 슬라이더 추가
- 프레임 처리 간격 슬라이더 추가
- `mlpackage / mlmodel / mlmodelc` 자동 탐색 추가
- 모델 미추가 시 상태 메시지 표시
- 카메라 오버레이 UI 정리

## 6. 참고

실제 탐지 품질은 결국 **내보낸 Core ML 모델 품질**에 따라 달라집니다.
즉, 이 zip은 **앱 측 온디바이스 실행 구조**를 완성한 버전이고,
실전 사용까지 가려면 학습된 YOLO 모델 파일을 같이 넣어야 합니다.

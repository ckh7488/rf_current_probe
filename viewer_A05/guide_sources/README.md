# A14/C07 단계별 조립 원본

2026-09-22 ·45단계·131메시·완성128표현 객체. 실제 native는125객체이고 자유 뚜껑·공구·개별 너트 표현 때문에 표시 수가 다르다. [현행 빌드](../README.md)를 따른다.

원본 native SHA256: `400618d82bd9f1d98a7f45a7e3e4bda1664310d61d81435e3d18fd1194b9e2a7`.

H05는 SMA만 선납땜하고 권선 끝선을 분리한 상태에서 PCB를 넣는다. 탈착 시 장착면에서0.3 mm 띄운 후45° 기울이고4 mm 아래 위치를 지나며, 삽입은 역순이다. PCB·M2×12 고정 후 H06에서 권선을 납땜한다. B05/B07 왼쪽 나사는25 mm 들어올린 후 바깥쪽으로 뺀다.

`geometry_supplements_a14.json`은 출처 해시를 포함한다. `current_static_verification.json`과 공개 검증의 현재 생성 시각/입력 해시를 확인한다. `animation_path_review.json`, `pcb_insertion_review.json`, `static_verification.json`의 A13/36단계/30° 기록은 이력이며 현재 경로의 증거가 아니다.

현행 최대 PCB/SMA 경로 근거는 [제출 전 검토](../../reviews/pre_jlc_review_20260922/README.md), 재생성 근거는 [전수 조사](../../reviews/document_full_audit_20260922/README.md)다. 강체 CAD 경로와 실제 손·유연한 권선·조임력 검증은 구별한다. 주석은 전역으로 숨길 수 있고 단계별 검증 범위는 펼쳐 볼 수 있다.

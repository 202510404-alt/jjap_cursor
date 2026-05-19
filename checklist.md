🏗️ Jjap-Cursor Implementation Checklist
지침: [MVP] 항목에만 집중하십시오. [Planned] 항목은 설계 구조만 유지하고 실제 구현은 다음 단계로 미룹니다. 모든 작업은 기존 ProjectManager와 ContextBuilder 구조를 계승합니다.
❗주의: 현재 프로젝트는 Scan + Plan 생성까지만 구현됨. [Phase A/B] 완료 전까지 UI 구현을 엄격히 금지함.
🟦 [Phase A] 실행 엔진 및 트랜잭션 (MVP - 최우선)
[ ] Multi-file Transaction Manager 구현

[ ] with transaction(): 형태의 컨텍스트 매니저 클래스 설계.

[ ] 수정 대상 파일들에 대한 .bak 백업 생성 및 에러 시 자동 rollback 로직.

[ ] Atomic write를 보장하는 최종 commit 프로세스.

[ ] Temp Workspace Patch 시스템

[ ] 실제 파일 대신 메모리 또는 임시 디렉토리에서 수정을 수행하는 PatchBuffer 구현.

[ ] line-range 기반의 1차 패치 로직 (AST 직접 수정 대신 텍스트 블록 교체 우선).

🟩 [Phase B] 안전장치 및 승인 게이트 (MVP)
[ ] Unified Diff Generator 구현

[ ] difflib 등을 활용하여 변경 사항을 표준 Diff 형식으로 추출하는 기능.

[ ] AI가 생성한 계획과 실제 패치 결과물의 정합성 확인.

[ ] Explicit Approval Gate (CLI 우선)

[ ] 생성된 Diff를 출력하고 사용자의 Y/N 입력을 대기하는 인터럽트 로직.

[ ] 승인 시에만 Transaction.commit() 호출, 거절 시 rollback.

🟨 [Phase C] 컨텍스트 엔진 보강 (MVP)
[ ] Token Budgeter 정교화

[ ] estimate_tokens 오차 범위 축소 및 실시간 예산 추적.

[ ] 우선순위(Target > Symbols > Facts > Skeletons)에 따른 Eviction 로직 고도화.

[ ] Light Validation Pipeline

[ ] 패치 적용 후 ast.parse()를 통한 문법 오류(Syntax Error) 자동 검증.

🟧 [Phase D] 구조 안정화 (Planned - 기반만 마련)
[ ] Self-Correction Loop 기초

[ ] 검증 실패 시 에러 메시지를 AI에게 재전송하는 루프 구조 (최대 3회).

[ ] Heuristic Metadata 개선

[ ] used_by 및 call-graph 추출 정확도 향상 (Namespace 체크 보강).

⬜ [Phase E] 인터페이스 확장 (Long-Term - 구현 금지)
[ ] Desktop UI를 위한 기초 API 엔드포인트 설계 예약.

[ ] ai_briefing.md TTL 기반 사실(Fact) 기록 정책 수립.
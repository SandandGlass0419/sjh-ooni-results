# sjh-ooni-results
Contains OONI's web connectivity test results for Seoul Sejong Highschool.

## 언제부터 측정했나요?
2026-03-04일 부터 측정했다. 주말은 제외하고, 2일에 한번씩 측정하고 있다.\
`Managed`에 있는 데이터는 월, 수, 금에 측정하고,\
`Unmanaged`에 있는 데이터는 화, 목에 측정한다.

## `Managed`랑 `Unmanaged`는 뭐가 다른가요?
`Managed`의 데이터는 mdm이 설치된 기기에서 측정한 결과이다.\
mdm이 지정된 dns를 사용하도록 프로그래밍 되었다고 추측했기 때문에 측정 결과를 분리했다.\
`Managed` 데이터는 4월부터 측정하기 시작했기 때문에 3월 데이터는 없다.\
`Unmanged`는 아무런 mdm 또는 관련 통제 소프트웨어가 설치되지 않은 기기에서 측정한 결과이다.

## `Unmanaged`의 `DNS`와 `No DNS`는 뭐가 다른가요?
`No DNS`는 안드로이드의 DNS서버 설정이 자동으로 설정된 상태에서 측정한 것이다. 3월에만 측정했다.\
결론적으로 `No DNS`와 `Managed`사이에 결과 차이가 없어서 내부 DNS를 사용할때 측정 결과가 궁금하다면 이 둘을 보면 된다.\
`DNS`는 안드로이드의 DNS서버 설정을 수동으로 설정하고, [dns.google](dns.google) 서버를 사용해 측정한 것이다. 4월부터 측정했다.

## 각 결과가 가지는 의미는 뭔가요?
- `ok`: 아무런 이상(anomaly) 없음.
- `dns`: "dns tampering"으로 불리며, ooni 서버에서 측정한 dns 처리 결과와 네트워크에서 측정된 처리 결과를 비교할때 이상이 발견됨.
- `tcp_ip`: 네트워크에서 tcp 연결에서 이상이 발견됨.
- `http-diff`: http 수신 내용이 ooni 서버에서 측정한 것과 달라 이상이 발견됨. (주로 잘 알려지지 않은 접근 거부 페이지를 감지)
- `http-failure`: http 요청이 실패하여 이상이 발견됨.
- `confirmed`: 접근 제한이 확실히 확인됨. (주로 [warning.or.gov](warning.or.gov) 처럼 잘 알려진 접근 거부 페이지를 감지)
- `error`: ooni 도구의 사이트 시험이 실패함.
- `no_data`: api 서버에서 정보를 가져오지 못함. ooni의 시험 결과는 아니다. (시험 결과가 업로드 되지 않았거나, 찾지 못했을때 사용)
- `http`: http 관련 이상이 발생했을때 사용했음. 지금은 대체되었다.

## `exporter.py`는 어떻게 사용하나요?
1. 기록할 시험들의 report_id를 찾아 csv 파일에 ("report_id", "시험 사이트 개수") 형식으로 기록한다.
2. `exporter.py`에서 `OUT_DIR`를 설정한다.
3. `exporter.py`에서 `ID_LIST_PATH`를 1에서 기록한 파일의 경로로 설정한다.
4. 실행

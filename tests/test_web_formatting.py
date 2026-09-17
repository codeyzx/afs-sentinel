from datetime import date, datetime, timezone
from types import SimpleNamespace

from afs.web import formatting as fmt
from afs.web.backtest_view import CaseEvent, claim_sentence, load_cases, months_between


def test_wib_formatting_treats_naive_as_utc():
    assert fmt.fmt_wib(datetime(2026, 9, 19, 1, 0)) == "19 Sep 2026, 08:00 WIB"
    assert fmt.fmt_wib(datetime(2026, 9, 19, 1, 0, tzinfo=timezone.utc), with_day=True) == "Sabtu, 19 Sep 2026, 08:00 WIB"


def test_number_formatting():
    assert fmt.fmt_num(12345.678, 2) == "12.345,68"
    assert fmt.fmt_score(75.0) == "75,0"
    assert fmt.fmt_finding_value("SLOAN_ACCRUAL", 0.138) == "13,8%"
    assert fmt.fmt_finding_value("ALTMAN_Z_ADAPTED", 1.42) == "Z = 1,42"
    assert fmt.fmt_finding_value("SLOAN_ACCRUAL", None) == "—"


def test_next_scheduled_run_is_saturday_0800_wib():
    friday = datetime(2026, 9, 18, 10, 0, tzinfo=timezone.utc)
    assert fmt.fmt_wib(fmt.next_scheduled_run(friday), with_day=True) == "Sabtu, 19 Sep 2026, 08:00 WIB"
    saturday_after = datetime(2026, 9, 19, 2, 0, tzinfo=timezone.utc)  # 09:00 WIB
    assert fmt.fmt_wib(fmt.next_scheduled_run(saturday_after)) == "26 Sep 2026, 08:00 WIB"


def test_months_between():
    assert months_between(date(2021, 6, 30), date(2023, 5, 8)) == 22
    assert months_between(date(2021, 3, 31), date(2021, 5, 18)) == 1


def test_claim_sentence():
    event = CaseEvent(date=date(2023, 5, 8), label="suspensi")
    rows = [SimpleNamespace(report_date=date(2021, 3, 31), severity="LOW"),
            SimpleNamespace(report_date=date(2021, 6, 30), severity="MODERATE")]
    assert claim_sentence(rows, event) == "Pertama kali Sedang: 2021-Q2, 22 bulan sebelum suspensi"
    late = CaseEvent(date=date(2021, 5, 1), label="x")
    assert claim_sentence(rows, late) == "Tidak terdeteksi lebih awal"


def test_load_cases_handles_missing_and_bad_files(tmp_path):
    assert load_cases(tmp_path / "none.json") == []
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    assert load_cases(bad) == []

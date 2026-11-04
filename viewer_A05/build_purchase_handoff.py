"""Retired purchase generator. Current sources: docs/BOM_DRAFT.md and dated procurement records.

DEC-053: the old generator removed two fixture SMAs and could recreate obsolete
fixture-rejection pages. Its exact source is preserved under
reviews/a03_500mhz_cleanup_20260923/before/viewer_A05/.
"""

def build(*args, **kwargs):
    raise RuntimeError("구형 구매 페이지 생성기는 폐기했습니다. 현행 A03 및 SMA3개 기준은 docs/BOM_DRAFT.md를 사용하세요. 가격·카트 기록은 날짜를 확인하세요.")


def build_impedance(*args, **kwargs):
    raise RuntimeError("구형 지그 판정 페이지는 폐기했습니다. viewer_A05/build_document_set.py가 현행 A03 보정 문서를 생성합니다.")


if __name__ == "__main__":
    build()

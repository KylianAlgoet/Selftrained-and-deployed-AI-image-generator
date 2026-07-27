from ml.dataset.manifest import load_manifest, save_manifest, validate_manifest
from ml.dataset.tests.conftest import valid_row


def test_valid_rows_pass():
    rows = [valid_row(), valid_row(id="DS-0002", sha256="b" * 64)]
    assert validate_manifest(rows) == []


def test_missing_required_field_reported():
    errors = validate_manifest([valid_row(caption="")])
    assert len(errors) == 1
    assert "caption" in errors[0]


def test_empty_author_and_notes_allowed():
    assert validate_manifest([valid_row(author="", notes="")]) == []


def test_licence_allowlist_enforced():
    errors = validate_manifest([valid_row(licence="CC-BY-NC")])
    assert any("licence" in e for e in errors)


def test_style_and_split_enforced():
    errors = validate_manifest([valid_row(style="graffiti"), valid_row(id="DS-0002", sha256="b" * 64, split="test")])
    assert any("style" in e for e in errors)
    assert any("split" in e for e in errors)


def test_duplicate_id_and_sha_reported():
    errors = validate_manifest([valid_row(), valid_row()])
    assert any("duplicate id" in e for e in errors)
    assert any("duplicate sha256" in e for e in errors)


def test_round_trip_save_load(tmp_path):
    path = tmp_path / "manifest.csv"
    rows = [valid_row(), valid_row(id="DS-0002", sha256="b" * 64)]
    save_manifest(rows, path)
    loaded = load_manifest(path)
    assert loaded == rows

from ml.dataset.generate_geometric import CANVAS_SIZE, config_note, generate_geometric
from ml.dataset.hashing import sha256_file
from ml.dataset.validate import validate_image


def test_same_seed_produces_identical_bytes(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    config_a = generate_geometric(1234, a)
    config_b = generate_geometric(1234, b)
    assert sha256_file(a) == sha256_file(b)
    assert config_a == config_b


def test_different_seeds_differ(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    generate_geometric(1, a)
    generate_geometric(2, b)
    assert sha256_file(a) != sha256_file(b)


def test_output_passes_project_validation(tmp_path):
    path = tmp_path / "gen.png"
    generate_geometric(99, path)
    result = validate_image(path)
    assert result.ok
    assert (result.width, result.height) == CANVAS_SIZE


def test_config_note_is_reproducible_provenance(tmp_path):
    config = generate_geometric(77, tmp_path / "x.png")
    note = config_note(config)
    assert "seed=77" in note
    assert "generate_geometric.py" in note

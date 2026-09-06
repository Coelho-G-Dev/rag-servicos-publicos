import json
from pathlib import Path


def test_seed_dataset_integrity():
    seed_path = Path(__file__).resolve().parent.parent / "data" / "servicos_seed.json"
    assert seed_path.exists(), f"Seed dataset não encontrado em {seed_path}"

    with open(seed_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert 40 <= len(data) <= 50, f"Esperado entre 40 e 50 registros, obtido: {len(data)}"

    required_keys = {"id", "nome", "categoria", "descricao", "endereco"}
    ids = set()

    for item in data:
        assert required_keys.issubset(item.keys()), f"Item com chaves ausentes: {item}"
        assert item["id"] not in ids, f"ID duplicado: {item['id']}"
        ids.add(item["id"])
        assert len(item["nome"].strip()) > 0
        assert len(item["categoria"].strip()) > 0
        assert len(item["descricao"].strip()) > 0
        assert len(item["endereco"].strip()) > 0

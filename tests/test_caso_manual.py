"""Pruebas del caso de comprobación manual (data/caso_manual.json)."""

from pathlib import Path

from src.red import Red

CASO_MANUAL = Path(__file__).resolve().parent.parent / "data" / "caso_manual.json"


def test_el_caso_manual_es_una_red_valida_de_4_a_6_centros():
    red = Red.cargar(CASO_MANUAL)

    assert 4 <= len(red.vertices) <= 6
    assert (red.origen, red.destino) == ("O", "T")
    assert all(isinstance(arco.capacidad, int) for arco in red.arcos())

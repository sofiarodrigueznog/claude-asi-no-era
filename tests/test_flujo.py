"""Pruebas del algoritmo de Edmonds–Karp (src/flujo.py)."""

from pathlib import Path

import pytest

from src.flujo import edmonds_karp
from src.red import Red

RED_INICIAL = Path(__file__).resolve().parent.parent / "data" / "red_inicial.json"


ARCOS_FIGURA_1 = [
    ("O", "A", 8), ("O", "B", 6), ("A", "C", 5), ("A", "D", 3),
    ("B", "D", 6), ("C", "T", 5), ("D", "T", 9),
]


def red_inicial():
    return Red.cargar(RED_INICIAL)


def red_figura_1():
    """Red de ejemplo del enunciado (Figura 1, página 1). Solo vive en esta prueba."""
    arcos = []
    for origen, destino, capacidad in ARCOS_FIGURA_1:
        arcos.append({"origen": origen, "destino": destino, "capacidad": capacidad})
    return Red({
        "vertices": ["O", "A", "B", "C", "D", "T"],
        "arcos": arcos,
        "origen": "O",
        "destino": "T",
    })


def flujo_neto(flujo, centro):
    """Entradas: flujo por arco y un centro. Resultado: lo que sale menos lo que entra."""
    neto = 0
    for (u, v), cantidad in flujo.items():
        if u == centro:
            neto += cantidad
        if v == centro:
            neto -= cantidad
    return neto


def test_flujo_maximo_de_la_figura_1_es_14():
    # 5 por O→A→C→T, 3 por O→A→D→T y 6 por O→B→D→T; el corte S={O} da 8 + 6 = 14.
    valor, flujo = edmonds_karp(red_figura_1(), "O", "T")
    assert valor == 14
    assert flujo[("O", "A")] == 8
    assert flujo[("O", "B")] == 6


def test_flujo_maximo_de_la_red_inicial_es_25():
    # Corte mínimo que lo confirma: {D→H, E→H, E→I, F→I, C→G} = 7 + 3 + 3 + 6 + 6 = 25.
    valor, _ = edmonds_karp(red_inicial(), "O", "T")
    assert valor == 25


def test_flujo_respeta_capacidades_y_conservacion():
    red = red_inicial()
    valor, flujo = edmonds_karp(red, "O", "T")

    for arco in red.arcos():
        assert 0 <= flujo[(arco.origen, arco.destino)] <= arco.capacidad

    for centro in red.vertices:
        if centro == "O":
            assert flujo_neto(flujo, centro) == valor
        elif centro == "T":
            assert flujo_neto(flujo, centro) == -valor
        else:
            assert flujo_neto(flujo, centro) == 0


def test_flujo_solo_trae_arcos_activos():
    red = red_inicial()
    red.desactivar_ruta("H", "T")
    _, flujo = edmonds_karp(red, "O", "T")
    assert ("H", "T") not in flujo
    assert len(flujo) == 17


def test_sin_camino_el_flujo_es_cero():
    red = red_inicial()
    for origen in ("G", "H", "I"):
        red.desactivar_ruta(origen, "T")
    valor, flujo = edmonds_karp(red, "O", "T")
    assert valor == 0
    for cantidad in flujo.values():
        assert cantidad == 0


def test_origen_igual_al_destino_falla():
    with pytest.raises(ValueError):
        edmonds_karp(red_inicial(), "O", "O")

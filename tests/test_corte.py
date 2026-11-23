"""Pruebas del corte mínimo (src/corte.py)."""

from pathlib import Path

import pytest

from src.corte import corte_minimo
from src.flujo import edmonds_karp
from src.red import Red

RED_INICIAL = Path(__file__).resolve().parent.parent / "data" / "red_inicial.json"

ARCOS_FIGURA_1 = [
    ("O", "A", 8),
    ("O", "B", 6),
    ("A", "C", 5),
    ("A", "D", 3),
    ("B", "D", 6),
    ("C", "T", 5),
    ("D", "T", 9),
]


def red_inicial():
    return Red.cargar(RED_INICIAL)


def red_figura_1():
    """Red de ejemplo del enunciado (Figura 1, página 1). Solo vive en esta prueba."""
    return Red(
        {
            "vertices": ["O", "A", "B", "C", "D", "T"],
            "arcos": [
                {"origen": u, "destino": v, "capacidad": c}
                for u, v, c in ARCOS_FIGURA_1
            ],
            "origen": "O",
            "destino": "T",
        }
    )


def test_corte_de_la_red_inicial():
    red = red_inicial()
    valor, flujo = edmonds_karp(red, "O", "T")

    lado_s, lado_t, arcos, capacidad = corte_minimo(red, flujo, "O")

    assert capacidad == valor == 25
    assert lado_s == {"O", "A", "B", "C", "D", "E", "F"}
    assert lado_t == {"G", "H", "I", "T"}
    assert arcos == [("C", "G"), ("D", "H"), ("E", "H"), ("E", "I"), ("F", "I")]


def test_la_particion_separa_el_origen_del_destino():
    red = red_inicial()
    valor, flujo = edmonds_karp(red, "A", "T")
    lado_s, lado_t, arcos, capacidad = corte_minimo(red, flujo, "A")

    assert capacidad == valor
    assert "A" in lado_s and "T" in lado_t
    assert lado_s | lado_t == set(red.vertices)
    assert not lado_s & lado_t
    assert all(u in lado_s and v in lado_t for u, v in arcos)
    assert capacidad == sum(red.capacidad(u, v) for u, v in arcos)


def test_corte_maximo_minimo_en_otra_red():
    red = red_figura_1()
    valor, flujo = edmonds_karp(red, "O", "T")

    lado_s, lado_t, arcos, capacidad = corte_minimo(red, flujo, "O")

    assert valor == 14
    assert capacidad == valor
    assert "O" in lado_s and "T" in lado_t
    assert all(u in lado_s and v in lado_t for u, v in arcos)


def test_una_ruta_desactivada_no_puede_estar_en_el_corte():
    red = red_inicial()
    red.desactivar_ruta("D", "H")
    valor, flujo = edmonds_karp(red, "O", "T")
    _, _, arcos, capacidad = corte_minimo(red, flujo, "O")

    assert ("D", "H") not in arcos
    assert capacidad == valor


def test_corte_con_cualquier_origen_y_destino():
    # El destino elegido puede no ser el destino guardado en la red (T).
    red = red_inicial()
    for s in red.vertices:
        for t in red.vertices:
            if s == t:
                continue
            valor, flujo = edmonds_karp(red, s, t)
            lado_s, lado_t, arcos, capacidad = corte_minimo(red, flujo, s, t)

            assert capacidad == valor
            assert s in lado_s and t in lado_t
            assert all(u in lado_s and v in lado_t for u, v in arcos)


def test_rechaza_un_centro_que_no_esta_en_la_red():
    red = red_inicial()
    _, flujo = edmonds_karp(red, "O", "T")

    with pytest.raises(ValueError, match="centro de la red"):
        corte_minimo(red, flujo, "Z")


def test_rechaza_un_flujo_que_todavia_no_es_maximo():
    red = red_inicial()
    flujo_cero = {(a.origen, a.destino): 0 for a in red.arcos(solo_activos=True)}

    with pytest.raises(ValueError, match="no es máximo"):
        corte_minimo(red, flujo_cero, "O", "T")


@pytest.mark.parametrize(
    "flujo, mensaje",
    [
        ({("O", "A"): -1}, "entre 0 y"),
        ({("O", "A"): 99}, "entre 0 y"),
        ({("Z", "A"): 1}, "ruta inexistente"),
        ({("O", "A"): 1.5}, "entero"),
    ],
)
def test_rechaza_un_flujo_invalido(flujo, mensaje):
    red = red_inicial()

    with pytest.raises(ValueError, match=mensaje):
        corte_minimo(red, flujo, "O")

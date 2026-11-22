"""Pruebas del resultado de prueba (se borran junto con src/resultado_prueba.py)."""

from itertools import permutations

import pytest

from src.red import Red
from src.resultado_prueba import ARCHIVO_RED, corte_minimo, edmonds_karp


@pytest.fixture
def red():
    return Red.cargar(ARCHIVO_RED)


def test_resultado_de_la_red_inicial(red):
    valor, flujo = edmonds_karp(red, "O", "T")
    lado_s, lado_t, arcos, capacidad = corte_minimo(red, flujo, "O")

    assert valor == capacidad == 25
    assert lado_s == {"O", "A", "B", "C", "D", "E", "F"}
    assert lado_t == {"G", "H", "I", "T"}
    assert arcos == [("C", "G"), ("D", "H"), ("E", "H"), ("E", "I"), ("F", "I")]


def test_el_flujo_de_prueba_es_valido(red):
    _, flujo = edmonds_karp(red, "O", "T")

    assert set(flujo) == {(a.origen, a.destino) for a in red.arcos(solo_activos=True)}
    assert all(0 <= x <= red.capacidad(u, v) for (u, v), x in flujo.items())
    for centro in set(red.vertices) - {"O", "T"}:
        entra = sum(x for (_, v), x in flujo.items() if v == centro)
        sale = sum(x for (u, _), x in flujo.items() if u == centro)
        assert entra == sale


def test_no_inventa_resultados_para_otros_pares(red):
    for s, t in permutations(red.vertices, 2):
        if (s, t) != ("O", "T"):
            with pytest.raises(NotImplementedError):
                edmonds_karp(red, s, t)


@pytest.mark.parametrize(
    "modificar",
    [
        lambda red: red.desactivar_ruta("C", "G"),
        lambda red: red.cambiar_capacidad("O", "A", 5),
        lambda red: red.agregar_conexion("O", "T", 3),
    ],
)
def test_no_inventa_resultados_para_redes_modificadas(red, modificar):
    _, flujo = edmonds_karp(red, "O", "T")
    modificar(red)
    with pytest.raises(NotImplementedError):
        edmonds_karp(red, "O", "T")
    with pytest.raises(NotImplementedError):
        corte_minimo(red, flujo, "O")

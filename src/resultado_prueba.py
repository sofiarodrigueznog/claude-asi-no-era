"""
Resultado de prueba para la interfaz mientras no estén `src/flujo.py` y `src/corte.py`.

Tiene las firmas acordadas para esos módulos, pero no calcula nada: solo conoce el resultado
verificado de la red inicial con O como origen y T como destino. En cualquier otro caso avisa
que no hay resultado, para no mostrar un valor falso.
"""

from __future__ import annotations

from pathlib import Path

from src.red import Red

ARCHIVO_RED = Path(__file__).resolve().parent.parent / "data" / "red_inicial.json"
SIN_RESULTADO = (
    "Solo hay resultado de prueba para la red inicial de O a T. "
    "Los demás casos estarán disponibles cuando esté el algoritmo."
)

# Flujo máximo verificado de la red inicial (valor 25).
FLUJO_PRUEBA: dict[tuple[str, str], int] = {
    ("O", "A"): 11,
    ("O", "B"): 8,
    ("O", "C"): 6,
    ("A", "D"): 6,
    ("A", "E"): 5,
    ("B", "D"): 2,
    ("B", "F"): 6,
    ("C", "F"): 0,
    ("C", "G"): 6,
    ("D", "H"): 7,
    ("D", "E"): 1,
    ("E", "H"): 3,
    ("E", "I"): 3,
    ("F", "I"): 6,
    ("G", "I"): 1,
    ("G", "T"): 5,
    ("H", "T"): 10,
    ("I", "T"): 10,
}
LADO_S = {"O", "A", "B", "C", "D", "E", "F"}


def _es_red_inicial(red: Red) -> bool:
    """
    Entradas: una red.
    Resultado: True si es igual a la red inicial, sin modificaciones.
    """
    return red.a_dict() == Red.cargar(ARCHIVO_RED).a_dict()


def edmonds_karp(red: Red, s: str, t: str) -> tuple[int, dict[tuple[str, str], int]]:
    """
    Entradas: la red, el origen s y el destino t.
    Resultado: (valor_maximo, flujo), con flujo = {(u, v): x(u, v)}. Lanza NotImplementedError
    si el caso no es la red inicial de O a T.
    """
    if (s, t) != ("O", "T") or not _es_red_inicial(red):
        raise NotImplementedError(SIN_RESULTADO)
    valor = sum(x for (u, _), x in FLUJO_PRUEBA.items() if u == s)
    return valor, dict(FLUJO_PRUEBA)


def corte_minimo(
    red: Red, flujo: dict[tuple[str, str], int], s: str
) -> tuple[set[str], set[str], list[tuple[str, str]], int]:
    """
    Entradas: la red, su flujo máximo y el origen s.
    Resultado: (S, T, arcos_corte, capacidad_corte). Lanza NotImplementedError si no
    corresponde al resultado de prueba.
    """
    if s != "O" or flujo != FLUJO_PRUEBA or not _es_red_inicial(red):
        raise NotImplementedError(SIN_RESULTADO)
    lado_t = set(red.vertices) - LADO_S
    arcos = [
        (a.origen, a.destino)
        for a in red.arcos(solo_activos=True)
        if a.origen in LADO_S and a.destino in lado_t
    ]
    return set(LADO_S), lado_t, arcos, sum(red.capacidad(u, v) for u, v in arcos)

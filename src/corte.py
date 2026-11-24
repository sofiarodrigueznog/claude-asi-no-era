"""
Corte mínimo asociado a un flujo máximo.

Dado un flujo x sobre la red, el grafo residual tiene:

- un arco hacia adelante u → v con capacidad c(u, v) - x(u, v), y
- un arco hacia atrás v → u con capacidad x(u, v).

Recorriendo con BFS desde el origen s los arcos con capacidad residual positiva
se obtiene el conjunto S de vértices alcanzables. El complemento es T, y los
arcos originales que van de S a T forman un corte s-t. Cuando el flujo es
máximo (no queda camino de aumento hasta t), ese corte es mínimo y su
capacidad coincide con el valor del flujo (teorema max-flow min-cut).

Solo se usan estructuras básicas de Python (dict, list, deque).
"""

from __future__ import annotations

from collections import deque

from src.red import Red
from src.verificacion import calcular_valor_flujo

Flujo = dict[tuple[str, str], int]
GrafoResidual = dict[str, dict[str, int]]


def construir_residual(red: Red, flujo: Flujo) -> GrafoResidual:
    """
    Entradas: la red y el flujo por arco {(u, v): x(u, v)}. Un arco que no aparece
    en el dict se toma con flujo 0.
    Resultado: grafo residual {u: {v: capacidad_residual}}, con los arcos hacia
    adelante y hacia atrás de cada ruta activa. Lanza ValueError si el flujo no es
    válido (centros o rutas desconocidas, o caudal fuera de [0, capacidad]).
    """
    for (u, v), cantidad in flujo.items():
        if not red.existe_ruta(u, v):
            raise ValueError(f"El flujo usa la ruta inexistente {u} → {v}.")
        if not isinstance(cantidad, int) or isinstance(cantidad, bool):
            raise ValueError(f"El flujo de {u} → {v} debe ser un número entero.")
        if not 0 <= cantidad <= red.capacidad(u, v):
            raise ValueError(
                f"El flujo de {u} → {v} debe estar entre 0 y {red.capacidad(u, v)} "
                f"(se recibió {cantidad})."
            )

    residual: GrafoResidual = {centro: {} for centro in red.vertices}
    for arco in red.arcos(solo_activos=True):
        u, v = arco.origen, arco.destino
        cantidad = flujo.get((u, v), 0)
        residual[u][v] = residual[u].get(v, 0) + (arco.capacidad - cantidad)
        residual[v][u] = residual[v].get(u, 0) + cantidad

    return residual


def alcanzables(residual: GrafoResidual, s: str) -> set[str]:
    """
    Entradas: grafo residual y el centro origen s.
    Resultado: conjunto de centros alcanzables desde s usando solo arcos con
    capacidad residual positiva.
    """
    visitados = {s}
    pendientes = deque([s])

    while pendientes:
        actual = pendientes.popleft()
        for vecino, capacidad_residual in residual[actual].items():
            if capacidad_residual > 0 and vecino not in visitados:
                visitados.add(vecino)
                pendientes.append(vecino)

    return visitados


def corte_minimo(
    red: Red, flujo: Flujo, s: str, t: str | None = None
) -> tuple[set[str], set[str], list[tuple[str, str]], int]:
    """
    Entradas: la red, su flujo máximo de s a t, el origen s y, opcionalmente, el
    destino t con que se calculó ese flujo (puede ser cualquier centro, no solo el
    destino guardado en la red).
    Resultado: (S, T, arcos_corte, capacidad_corte), donde S es el conjunto de
    vértices alcanzables en el residual, T su complemento, arcos_corte las rutas
    activas que van de S a T y capacidad_corte la suma de sus capacidades.
    Lanza ValueError si s o t no están en la red, o si se da t y el flujo aún admite
    un camino de aumento hasta t (en ese caso no es máximo y no define un corte
    mínimo).
    """
    if s not in red.vertices:
        raise ValueError("El origen del corte debe ser un centro de la red.")
    if t is not None and t not in red.vertices:
        raise ValueError("El destino del corte debe ser un centro de la red.")

    residual = construir_residual(red, flujo)
    lado_s = alcanzables(residual, s)
    if t is not None and t in lado_s:
        raise ValueError(
            "El flujo no es máximo: todavía hay un camino de aumento hasta el destino."
        )

    lado_t = set(red.vertices) - lado_s
    arcos = [
        (arco.origen, arco.destino)
        for arco in red.arcos(solo_activos=True)
        if arco.origen in lado_s and arco.destino in lado_t
    ]
    capacidad = sum(red.capacidad(u, v) for u, v in arcos)

    comprobar_capacidad_igual_al_flujo(capacidad, flujo, s)

    return lado_s, lado_t, arcos, capacidad


def comprobar_capacidad_igual_al_flujo(capacidad: int, flujo: Flujo, s: str) -> None:
    """
    Entradas: la capacidad del corte, el flujo por arco y el origen s.
    Resultado: ninguno; lanza ValueError si la capacidad del corte no coincide con el
    valor del flujo, porque en ese caso el flujo no es máximo.
    """
    valor_flujo = calcular_valor_flujo(flujo, s)
    if capacidad != valor_flujo:
        raise ValueError(
            f"La capacidad del corte ({capacidad}) no coincide con el valor del flujo "
            f"({valor_flujo}): el flujo no es máximo."
        )

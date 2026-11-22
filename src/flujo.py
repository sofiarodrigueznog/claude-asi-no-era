"""
Flujo máximo con el algoritmo de Edmonds–Karp.

Se trabaja sobre el grafo residual de la red: por cada arco activo u → v con
capacidad c(u, v) y flujo x(u, v) hay

- un arco hacia adelante u → v con capacidad residual c(u, v) - x(u, v), y
- un arco hacia atrás v → u con capacidad residual x(u, v).

En cada iteración se busca con BFS el camino de aumento más corto (en número de
arcos) de s a t y se aumenta el flujo en su cuello de botella. Cuando no quedan
caminos, el flujo es máximo.

Solo se usan estructuras básicas de Python (dict, list, deque).
"""

from __future__ import annotations

from collections import deque

from src.red import Red

GrafoResidual = dict[str, dict[str, int]]
Flujo = dict[tuple[str, str], int]


def construir_grafo_residual(red: Red) -> GrafoResidual:
    """
    Entradas: la red con sus capacidades.
    Resultado: grafo residual con flujo inicial cero, como dict
    {u: {v: capacidad residual}}. Cada arco activo u → v aporta capacidad c(u, v)
    hacia adelante y 0 hacia atrás. Las rutas desactivadas no aparecen.
    """
    residual: GrafoResidual = {}
    for centro in red.vertices:
        residual[centro] = {}

    for arco in red.arcos(solo_activos=True):
        residual[arco.origen][arco.destino] = arco.capacidad
        residual[arco.destino][arco.origen] = 0

    return residual


def buscar_camino_bfs(residual: GrafoResidual, s: str, t: str) -> list[str] | None:
    """
    Entradas: grafo residual, origen s y destino t.
    Resultado: lista de centros [s, ..., t] del camino de aumento con menos arcos,
    usando solo arcos con capacidad residual positiva; None si t no es alcanzable.
    """
    predecesor: dict[str, str | None] = {s: None}
    pendientes = deque([s])

    while pendientes:
        actual = pendientes.popleft()
        if actual == t:
            return reconstruir_camino(predecesor, t)

        for vecino, capacidad_residual in residual[actual].items():
            if capacidad_residual > 0 and vecino not in predecesor:
                predecesor[vecino] = actual
                pendientes.append(vecino)

    return None


def reconstruir_camino(predecesor: dict[str, str | None], t: str) -> list[str]:
    """
    Entradas: predecesor de cada centro visitado por la BFS (el origen tiene None)
    y el destino t.
    Resultado: el camino desde el origen hasta t, en orden.
    """
    camino = []
    actual: str | None = t
    while actual is not None:
        camino.append(actual)
        actual = predecesor[actual]
    camino.reverse()
    return camino


def calcular_cuello_de_botella(residual: GrafoResidual, camino: list[str]) -> int:
    """
    Entradas: grafo residual y un camino de aumento.
    Resultado: la menor capacidad residual entre los arcos del camino, que es
    cuánto flujo se puede enviar por él.
    """
    cuello = residual[camino[0]][camino[1]]
    for u, v in zip(camino, camino[1:]):
        if residual[u][v] < cuello:
            cuello = residual[u][v]
    return cuello


def aumentar_flujo(residual: GrafoResidual, camino: list[str], cantidad: int) -> None:
    """
    Entradas: grafo residual, camino de aumento y cantidad a enviar.
    Resultado: ninguno; modifica el grafo residual restando la cantidad en cada
    arco del camino y sumándola en el arco inverso.
    """
    for u, v in zip(camino, camino[1:]):
        residual[u][v] -= cantidad
        residual[v][u] += cantidad


def extraer_flujo(red: Red, residual: GrafoResidual) -> Flujo:
    """
    Entradas: la red original y el grafo residual final.
    Resultado: dict {(u, v): x(u, v)} sobre los arcos originales activos. El flujo
    de cada arco es la capacidad residual de su arco hacia atrás, porque la red
    no tiene arcos recíprocos.
    """
    flujo: Flujo = {}
    for arco in red.arcos(solo_activos=True):
        flujo[(arco.origen, arco.destino)] = residual[arco.destino][arco.origen]
    return flujo


def edmonds_karp(red: Red, s: str, t: str) -> tuple[int, Flujo]:
    """
    Entradas: la red, el origen s y el destino t (centros distintos de la red).
    Resultado: (valor_maximo, flujo), donde valor_maximo es el flujo máximo de s a
    t y flujo es un dict {(u, v): x(u, v)} sobre los arcos originales activos.
    Lanza ValueError si s o t no están en la red o son el mismo centro.
    """
    if s not in red.vertices or t not in red.vertices:
        raise ValueError("El origen y el destino deben ser centros de la red.")
    if s == t:
        raise ValueError("El origen y el destino deben ser centros distintos.")

    residual = construir_grafo_residual(red)
    valor_maximo = 0

    camino = buscar_camino_bfs(residual, s, t)
    while camino is not None:
        cantidad = calcular_cuello_de_botella(residual, camino)
        aumentar_flujo(residual, camino, cantidad)
        valor_maximo += cantidad
        camino = buscar_camino_bfs(residual, s, t)

    return valor_maximo, extraer_flujo(red, residual)

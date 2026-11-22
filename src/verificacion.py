"""
Comprobaciones de que un flujo calculado es válido.

Un flujo x sobre la red con origen s y destino t es válido si cumple:

- capacidad: 0 ≤ x(u, v) ≤ c(u, v) en todo arco, y
- conservación: en cada vértice distinto de s y t, lo que entra es igual a lo que sale.

Su valor es lo que sale de s menos lo que entra a s.

El flujo se recibe como dict {(u, v): x(u, v)}, el mismo formato que devuelve
`edmonds_karp`. Un arco que no aparece en el dict se toma con flujo 0. Las rutas
desactivadas tienen capacidad efectiva 0, así que no pueden llevar flujo.

Cada comprobación devuelve una lista de mensajes, vacía si todo está bien, para que la
interfaz pueda mostrar todos los problemas de una vez.
"""

from __future__ import annotations

from src.red import Red

Flujo = dict[tuple[str, str], int]


def verificar_capacidades(red: Red, flujo: Flujo) -> list[str]:
    """
    Entradas: la red y el flujo por arco.
    Resultado: un mensaje por cada arco con flujo negativo o mayor que su capacidad
    efectiva, y por cada arco del flujo que no existe en la red. Lista vacía si se
    cumple 0 ≤ x(u, v) ≤ c(u, v) en todo arco.
    """
    errores = []

    for (u, v), cantidad in flujo.items():
        if not red.existe_ruta(u, v):
            errores.append(f"El flujo usa la ruta {u} → {v}, que no existe en la red.")
            continue

        capacidad = red.capacidad(u, v)
        if cantidad < 0:
            errores.append(f"Ruta {u} → {v}: el flujo es negativo ({cantidad}).")
        elif cantidad > capacidad:
            errores.append(
                f"Ruta {u} → {v}: el flujo ({cantidad}) supera la capacidad ({capacidad})."
            )

    return errores


def calcular_balance(flujo: Flujo, centro: str) -> int:
    """
    Entradas: el flujo por arco y un centro.
    Resultado: lo que sale del centro menos lo que entra.
    """
    balance = 0
    for (u, v), cantidad in flujo.items():
        if u == centro:
            balance += cantidad
        if v == centro:
            balance -= cantidad
    return balance


def verificar_conservacion(red: Red, flujo: Flujo, s: str, t: str) -> list[str]:
    """
    Entradas: la red, el flujo por arco, el origen s y el destino t.
    Resultado: un mensaje por cada centro distinto de s y t donde lo que entra no es
    igual a lo que sale. Lista vacía si el flujo se conserva en todos ellos.
    """
    errores = []

    for centro in red.vertices:
        if centro == s or centro == t:
            continue
        balance = calcular_balance(flujo, centro)
        if balance > 0:
            errores.append(f"Centro {centro}: sale {balance} más de lo que entra.")
        elif balance < 0:
            errores.append(f"Centro {centro}: entra {-balance} más de lo que sale.")

    return errores


def calcular_valor_flujo(flujo: Flujo, s: str) -> int:
    """
    Entradas: el flujo por arco y el origen s.
    Resultado: el valor del flujo, es decir, lo que sale de s menos lo que entra a s.
    """
    return calcular_balance(flujo, s)


def verificar_flujo(red: Red, flujo: Flujo, s: str, t: str) -> list[str]:
    """
    Entradas: la red, el flujo por arco, el origen s y el destino t.
    Resultado: todos los problemas de capacidad y de conservación juntos. Lista vacía
    si el flujo es válido.
    """
    return verificar_capacidades(red, flujo) + verificar_conservacion(red, flujo, s, t)

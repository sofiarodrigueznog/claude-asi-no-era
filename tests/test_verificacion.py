"""Pruebas de las comprobaciones del flujo (src/verificacion.py)."""

from pathlib import Path

from src.red import Red
from src.verificacion import (
    calcular_valor_flujo,
    verificar_capacidades,
    verificar_conservacion,
    verificar_flujo,
)

RED_INICIAL = Path(__file__).resolve().parent.parent / "data" / "red_inicial.json"

ARCOS_FIGURA_1 = [
    ("O", "A", 8), ("O", "B", 6), ("A", "C", 5), ("A", "D", 3),
    ("B", "D", 6), ("C", "T", 5), ("D", "T", 9),
]

# Flujo máximo de la Figura 1: 5 por O→A→C→T, 3 por O→A→D→T y 6 por O→B→D→T.
FLUJO_FIGURA_1 = {
    ("O", "A"): 8, ("O", "B"): 6, ("A", "C"): 5, ("A", "D"): 3,
    ("B", "D"): 6, ("C", "T"): 5, ("D", "T"): 9,
}

# Flujo máximo de la red inicial: salen 11 + 8 + 6 = 25 de O.
FLUJO_RED_INICIAL = {
    ("O", "A"): 11, ("O", "B"): 8, ("O", "C"): 6, ("A", "D"): 6, ("A", "E"): 5,
    ("B", "D"): 2, ("B", "F"): 6, ("C", "F"): 0, ("C", "G"): 6, ("D", "H"): 7,
    ("D", "E"): 1, ("E", "H"): 3, ("E", "I"): 3, ("F", "I"): 6, ("G", "I"): 1,
    ("G", "T"): 5, ("H", "T"): 10, ("I", "T"): 10,
}


def red_figura_1():
    """Red de ejemplo del enunciado (Figura 1, página 1)."""
    arcos = []
    for origen, destino, capacidad in ARCOS_FIGURA_1:
        arcos.append({"origen": origen, "destino": destino, "capacidad": capacidad})
    return Red({
        "vertices": ["O", "A", "B", "C", "D", "T"],
        "arcos": arcos,
        "origen": "O",
        "destino": "T",
    })


def flujo_con(**cambios):
    """Copia de FLUJO_FIGURA_1 con arcos cambiados; la clave "AC" es el arco A → C."""
    flujo = dict(FLUJO_FIGURA_1)
    for nombre, cantidad in cambios.items():
        flujo[(nombre[0], nombre[1])] = cantidad
    return flujo


# ---- flujos válidos ------------------------------------------------------------------


def test_flujo_de_la_figura_1_es_valido_y_vale_14():
    red = red_figura_1()
    assert verificar_flujo(red, FLUJO_FIGURA_1, "O", "T") == []
    assert calcular_valor_flujo(FLUJO_FIGURA_1, "O") == 14


def test_flujo_verificado_de_la_red_inicial_es_valido_y_vale_25():
    red = Red.cargar(RED_INICIAL)
    assert verificar_flujo(red, FLUJO_RED_INICIAL, "O", "T") == []
    assert calcular_valor_flujo(FLUJO_RED_INICIAL, "O") == 25


def test_flujo_cero_es_valido():
    red = red_figura_1()
    flujo = {}
    for origen, destino, _ in ARCOS_FIGURA_1:
        flujo[(origen, destino)] = 0
    assert verificar_flujo(red, flujo, "O", "T") == []
    assert calcular_valor_flujo(flujo, "O") == 0


# ---- capacidad -----------------------------------------------------------------------


def test_detecta_flujo_mayor_que_la_capacidad():
    errores = verificar_capacidades(red_figura_1(), flujo_con(AC=6))
    assert len(errores) == 1
    assert "A → C" in errores[0]
    assert "supera la capacidad" in errores[0]


def test_detecta_flujo_negativo():
    errores = verificar_capacidades(red_figura_1(), flujo_con(AC=-1))
    assert len(errores) == 1
    assert "negativo" in errores[0]


def test_ruta_desactivada_no_puede_llevar_flujo():
    red = red_figura_1()
    red.desactivar_ruta("A", "C")
    errores = verificar_capacidades(red, FLUJO_FIGURA_1)
    assert len(errores) == 1
    assert "A → C" in errores[0]


def test_detecta_ruta_que_no_existe():
    flujo = dict(FLUJO_FIGURA_1)
    flujo[("C", "D")] = 1
    errores = verificar_capacidades(red_figura_1(), flujo)
    assert len(errores) == 1
    assert "no existe" in errores[0]


# ---- conservación --------------------------------------------------------------------


def test_detecta_centro_que_no_conserva():
    # A recibe 8 pero manda 4 + 3 = 7; C recibe 4 y manda 5.
    errores = verificar_conservacion(red_figura_1(), flujo_con(AC=4), "O", "T")
    assert len(errores) == 2
    assert "Centro A" in errores[0]
    assert "Centro C" in errores[1]


def test_origen_y_destino_no_necesitan_conservar():
    errores = verificar_conservacion(red_figura_1(), FLUJO_FIGURA_1, "O", "T")
    assert errores == []


# ---- valor del flujo -----------------------------------------------------------------


def test_valor_resta_lo_que_entra_al_origen():
    # Red pequeña con un arco que vuelve al origen: B → O.
    flujo = {("O", "A"): 5, ("A", "B"): 5, ("B", "O"): 2, ("B", "T"): 3}
    assert calcular_valor_flujo(flujo, "O") == 3


def test_verificar_flujo_junta_todos_los_problemas():
    errores = verificar_flujo(red_figura_1(), flujo_con(AC=6), "O", "T")
    # Capacidad en A → C, y conservación en A y en C.
    assert len(errores) == 3

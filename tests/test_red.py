"""Pruebas del modelo de la red (src/red.py)."""

import copy
import dataclasses
from pathlib import Path

import pytest

from src.red import Red, RedInvalidaError, validar_datos

RED_INICIAL = Path(__file__).resolve().parent.parent / "data" / "red_inicial.json"

# Red pequeña de 4 centros para las pruebas de validación y modificación.
BASE = {
    "vertices": ["O", "A", "B", "T"],
    "arcos": [
        {"origen": "O", "destino": "A", "capacidad": 4, "activa": True},
        {"origen": "O", "destino": "B", "capacidad": 3, "activa": True},
        {"origen": "A", "destino": "B", "capacidad": 2, "activa": True},
        {"origen": "A", "destino": "T", "capacidad": 3, "activa": True},
        {"origen": "B", "destino": "T", "capacidad": 5, "activa": True},
    ],
    "origen": "O",
    "destino": "T",
}


def datos_con(**cambios):
    """Copia de BASE con las claves indicadas reemplazadas."""
    datos = copy.deepcopy(BASE)
    datos.update(cambios)
    return datos


def con_arco(arco):
    """Copia de BASE con un arco extra al final."""
    datos = copy.deepcopy(BASE)
    datos["arcos"].append(arco)
    return datos


@pytest.fixture
def red():
    return Red(copy.deepcopy(BASE))


# ---- carga y guardado ----------------------------------------------------------------


def test_carga_la_red_inicial():
    red = Red.cargar(RED_INICIAL)
    assert len(red.vertices) == 11
    assert len(red.arcos()) == 18
    assert (red.origen, red.destino) == ("O", "T")
    assert red.sucesores("O") == ["A", "B", "C"]
    assert red.predecesores("T") == ["G", "H", "I"]


def test_guardar_respeta_el_formato_del_archivo():
    red = Red.cargar(RED_INICIAL)
    assert red.a_json() == RED_INICIAL.read_text(encoding="utf-8")


def test_guardar_y_cargar_conserva_los_cambios(red, tmp_path):
    red.desactivar_ruta("A", "B")
    red.cambiar_capacidad("O", "A", 7)
    red.agregar_conexion("O", "T", 1)
    archivo = tmp_path / "red.json"
    red.guardar(archivo)

    recargada = Red.cargar(archivo)
    assert recargada.a_dict() == red.a_dict()
    assert recargada.arco("A", "B").activa is False


def test_desde_json_acepta_bytes():
    texto = RED_INICIAL.read_bytes()
    assert len(Red.desde_json(texto).vertices) == 11


def test_activa_es_opcional_al_cargar():
    datos = copy.deepcopy(BASE)
    for arco in datos["arcos"]:
        del arco["activa"]
    assert all(arco.activa for arco in Red(datos).arcos())


def test_json_mal_escrito():
    with pytest.raises(RedInvalidaError, match="no es JSON válido"):
        Red.desde_json('{"vertices": [')


# ---- validaciones --------------------------------------------------------------------


def test_red_base_es_valida():
    assert validar_datos(BASE) == []


@pytest.mark.parametrize(
    "datos, mensaje",
    [
        ([], "objeto JSON"),
        ({"vertices": ["O"]}, "Faltan las claves: arcos, origen, destino"),
        (datos_con(vertices=[]), "al menos un centro"),
        (datos_con(vertices=["O", "A", "A", "B", "T"]), "Vértice A: está repetido"),
        (datos_con(vertices=["O", "A", "", "B", "T"]), "texto no vacío"),
        (datos_con(origen="X"), "El origen 'X' no está"),
        (datos_con(destino="O"), "deben ser centros distintos"),
        (con_arco({"origen": "B", "destino": "B", "capacidad": 1}), "es un lazo"),
        (con_arco({"origen": "O", "destino": "A", "capacidad": 1}), "O → A está repetida"),
        (con_arco({"origen": "B", "destino": "A", "capacidad": 1}), "recíproca de la ruta A → B"),
        (con_arco({"origen": "O", "destino": "Z", "capacidad": 1}), "no están en la lista de vértices: 'Z'"),
        (con_arco({"origen": "O", "destino": "T"}), "faltan las claves capacidad"),
        (con_arco({"origen": "O", "destino": "T", "capacidad": 0}), "entre 1 y 12 (se recibió 0)"),
        (con_arco({"origen": "O", "destino": "T", "capacidad": 13}), "entre 1 y 12 (se recibió 13)"),
        (con_arco({"origen": "O", "destino": "T", "capacidad": 2.5}), "número entero"),
        (con_arco({"origen": "O", "destino": "T", "capacidad": "5"}), "número entero"),
        (con_arco({"origen": "O", "destino": "T", "capacidad": True}), "número entero"),
        (con_arco({"origen": "O", "destino": "T", "capacidad": 1, "activa": "si"}), "true o false"),
        (datos_con(vertices=["O", "A", "B", "T", "X"]), "Vértice X: está aislado"),
        (datos_con(arcos="O->A"), "'arcos' debe ser una lista"),
    ],
)
def test_detecta_errores_de_modelacion(datos, mensaje):
    with pytest.raises(RedInvalidaError) as error:
        Red(datos)
    assert any(mensaje in e for e in error.value.errores), error.value.errores


def test_informa_todos_los_errores_juntos():
    datos = con_arco({"origen": "B", "destino": "B", "capacidad": 20})
    datos["vertices"].append("X")
    errores = validar_datos(datos)
    assert len(errores) == 3  # lazo, capacidad fuera de rango y vértice aislado


# ---- consultas -----------------------------------------------------------------------


def test_capacidad_es_cero_si_no_hay_ruta(red):
    assert red.capacidad("O", "A") == 4
    assert red.capacidad("A", "O") == 0
    assert red.capacidad("O", "T") == 0


def test_ruta_inexistente(red):
    assert not red.existe_ruta("O", "T")
    with pytest.raises(RedInvalidaError, match="No existe la ruta O → T"):
        red.arco("O", "T")


def test_centro_inexistente(red):
    with pytest.raises(RedInvalidaError, match="'Z' no está en la red"):
        red.sucesores("Z")


def test_los_arcos_no_se_modifican_por_fuera(red):
    with pytest.raises(dataclasses.FrozenInstanceError):
        red.arcos()[0].capacidad = 99


# ---- modificaciones ------------------------------------------------------------------


def test_desactivar_y_activar_ruta(red):
    red.desactivar_ruta("A", "T")
    assert red.capacidad("A", "T") == 0
    assert red.existe_ruta("A", "T")
    assert red.sucesores("A") == ["B"]
    assert len(red.arcos(solo_activos=True)) == 4

    red.activar_ruta("A", "T")
    assert red.capacidad("A", "T") == 3


def test_desactivar_ruta_inexistente(red):
    with pytest.raises(RedInvalidaError, match="No existe la ruta"):
        red.desactivar_ruta("T", "O")


def test_cambiar_capacidad(red):
    red.cambiar_capacidad("O", "B", 12)
    assert red.capacidad("O", "B") == 12


@pytest.mark.parametrize("capacidad", [0, 13, -1, 2.5, "4"])
def test_cambiar_capacidad_fuera_de_rango_no_modifica(red, capacidad):
    with pytest.raises(RedInvalidaError):
        red.cambiar_capacidad("O", "B", capacidad)
    assert red.capacidad("O", "B") == 3


def test_agregar_conexion(red):
    red.agregar_conexion("O", "T", 6)
    assert red.capacidad("O", "T") == 6
    assert red.arcos()[-1].destino == "T"


@pytest.mark.parametrize(
    "origen, destino, capacidad, mensaje",
    [
        ("A", "A", 1, "es un lazo"),
        ("O", "A", 1, "está repetida"),
        ("T", "A", 1, "recíproca"),
        ("O", "T", 0, "entre 1 y 12"),
        ("O", "Z", 1, "'Z' no está en la red"),
    ],
)
def test_agregar_conexion_invalida_no_modifica(red, origen, destino, capacidad, mensaje):
    antes = red.a_dict()
    with pytest.raises(RedInvalidaError, match=mensaje):
        red.agregar_conexion(origen, destino, capacidad)
    assert red.a_dict() == antes


def test_copia_es_independiente(red):
    copia = red.copia()
    copia.desactivar_ruta("O", "A")
    copia.agregar_conexion("O", "T", 2)
    assert red.capacidad("O", "A") == 4
    assert not red.existe_ruta("O", "T")

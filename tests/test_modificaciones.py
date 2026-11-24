"""Pruebas de las modificaciones de la red desde la interfaz (TOG-17)."""

from pathlib import Path

import pytest

import app
from app import ARCHIVO_RED, aplicar_accion, dividir_ruta
from src.corte import corte_minimo
from src.flujo import edmonds_karp
from src.red import Red
from src.verificacion import verificar_flujo

RUTA_APP = Path(app.__file__)


def red_inicial():
    return Red.cargar(ARCHIVO_RED)


def boton(interfaz, texto):
    """Busca un botón por su etiqueta, sin depender del orden en la interfaz."""
    return next(b for b in interfaz.button if texto in b.proto.label)


def control(interfaz, tipo, etiqueta):
    """Busca un widget por su etiqueta, sin depender del orden en la interfaz."""
    return next(w for w in getattr(interfaz, tipo) if w.proto.label == etiqueta)


def test_dividir_ruta():
    assert dividir_ruta("O → A") == ("O", "A")


def test_desactivar_ruta_no_modifica_la_original():
    red = red_inicial()

    nueva, errores = aplicar_accion(red, "desactivar", "O", "A")

    assert errores == []
    assert nueva.arco("O", "A").activa is False
    assert red.arco("O", "A").activa is True


def test_reactivar_ruta():
    desactivada, _ = aplicar_accion(red_inicial(), "desactivar", "O", "A")

    nueva, errores = aplicar_accion(desactivada, "activar", "O", "A")

    assert errores == []
    assert nueva.arco("O", "A").activa is True


def test_cambiar_capacidad_dentro_del_rango():
    red = red_inicial()

    nueva, errores = aplicar_accion(red, "capacidad", "O", "A", 7)

    assert errores == []
    assert nueva.arco("O", "A").capacidad == 7
    assert red.arco("O", "A").capacidad == 12


@pytest.mark.parametrize("capacidad", [0, 13])
def test_cambiar_capacidad_fuera_del_rango_devuelve_mensaje(capacidad):
    red = red_inicial()

    nueva, errores = aplicar_accion(red, "capacidad", "O", "A", capacidad)

    assert nueva is red
    assert any("capacidad" in mensaje for mensaje in errores)


def test_agregar_conexion_valida():
    red = red_inicial()

    nueva, errores = aplicar_accion(red, "agregar", "O", "T", 6)

    assert errores == []
    assert nueva.existe_ruta("O", "T")
    assert nueva.arco("O", "T").capacidad == 6
    assert not red.existe_ruta("O", "T")


@pytest.mark.parametrize(
    "origen, destino, palabra",
    [
        ("O", "O", "lazo"),
        ("O", "A", "repetida"),
        ("A", "O", "recíproca"),
    ],
)
def test_agregar_conexion_invalida_devuelve_mensaje(origen, destino, palabra):
    red = red_inicial()

    nueva, errores = aplicar_accion(red, "agregar", origen, destino, 6)

    assert nueva is red
    assert any(palabra in mensaje for mensaje in errores)


def test_el_flujo_se_recalcula_sobre_la_red_modificada():
    red = red_inicial()
    valor_inicial, _ = edmonds_karp(red, "O", "T")

    modificada, errores = aplicar_accion(red, "desactivar", "O", "A")
    assert errores == []

    valor, flujo = edmonds_karp(modificada, "O", "T")
    assert valor < valor_inicial
    assert flujo.get(("O", "A"), 0) == 0
    assert verificar_flujo(modificada, flujo, "O", "T") == []
    assert corte_minimo(modificada, flujo, "O", "T")[3] == valor


def test_la_interfaz_desactiva_y_recalcula():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    boton(interfaz, "Calcular flujo máximo").click().run()
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "25 paquetes/h"

    boton(interfaz, "Desactivar").click().run()
    assert not interfaz.error
    assert interfaz.success  # "Ruta desactivada."
    assert not interfaz.metric  # el resultado anterior se invalidó
    assert interfaz.info  # aviso de recalcular

    boton(interfaz, "Recalcular flujo").click().run()
    assert not interfaz.error
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] != "25 paquetes/h"


def test_la_interfaz_cambia_la_capacidad_y_lo_refleja_en_la_tabla():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    control(interfaz, "number_input", "Nueva capacidad (1–12)").set_value(7).run()
    boton(interfaz, "Cambiar capacidad").click().run()
    boton(interfaz, "Recalcular flujo").click().run()

    assert not interfaz.error
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "23 paquetes/h"
    tabla = interfaz.dataframe[0].value
    fila = tabla[tabla["Ruta"] == "O → A"].iloc[0]
    assert fila["Capacidad"] == 7


def test_la_interfaz_rechaza_una_conexion_reciproca():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    control(interfaz, "selectbox", "Origen").set_value("A").run()
    control(interfaz, "selectbox", "Destino").set_value("O").run()
    boton(interfaz, "Agregar conexión").click().run()

    assert any("recíproca" in e.value for e in interfaz.error)
    assert not interfaz.success


def test_la_interfaz_puede_restablecer_la_red():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    boton(interfaz, "Desactivar").click().run()
    boton(interfaz, "Restablecer red inicial").click().run()
    boton(interfaz, "Calcular flujo máximo").click().run()

    assert not interfaz.error
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "25 paquetes/h"


def test_los_botones_reflejan_el_cambio_al_instante():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    boton(interfaz, "Desactivar").click().run()

    # Sin otro clic: la ruta ya figura inactiva en los controles.
    assert boton(interfaz, "Desactivar").disabled
    assert not boton(interfaz, "Reactivar").disabled

    boton(interfaz, "Reactivar").click().run()
    assert not interfaz.error
    assert [s.value for s in interfaz.success] == ["Ruta reactivada."]
    assert not boton(interfaz, "Desactivar").disabled


def test_la_conexion_agregada_aparece_en_el_selector_de_rutas():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    control(interfaz, "selectbox", "Origen").set_value("O").run()
    control(interfaz, "selectbox", "Destino").set_value("T").run()
    boton(interfaz, "Agregar conexión").click().run()

    assert "O → T" in control(interfaz, "selectbox", "Ruta").options

    # Si estaba elegida y se restablece la red, el selector no se rompe.
    control(interfaz, "selectbox", "Ruta").set_value("O → T").run()
    boton(interfaz, "Restablecer red inicial").click().run()
    assert not interfaz.exception
    assert "O → T" not in control(interfaz, "selectbox", "Ruta").options


def test_el_mensaje_se_muestra_una_sola_vez():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    boton(interfaz, "Desactivar").click().run()
    assert [s.value for s in interfaz.success] == ["Ruta desactivada."]

    boton(interfaz, "Recalcular flujo").click().run()
    assert not interfaz.success

"""Pruebas de la comparación de configuraciones (TOG-18)."""

from pathlib import Path

import app
import pytest
from app import (
    ARCHIVO_RED,
    CONFIGURACIONES,
    CONFIGURACION_INICIAL,
    calcular_comparacion,
)
from src.red import Red

RUTA_APP = Path(app.__file__)


def boton(interfaz, texto):
    """Busca un botón por su etiqueta, sin depender del orden en la interfaz."""
    return next(b for b in interfaz.button if texto in b.proto.label)


def control(interfaz, tipo, etiqueta):
    """Busca un widget por su etiqueta, sin depender del orden en la interfaz."""
    return next(w for w in getattr(interfaz, tipo) if w.proto.label == etiqueta)


def test_hay_tres_configuraciones_con_archivos_validos():
    assert list(CONFIGURACIONES) == [
        CONFIGURACION_INICIAL,
        "Modificación 1 (sin O → A)",
        "Modificación 2 (O → T, cap. 6)",
    ]
    for nombre, ruta in CONFIGURACIONES.items():
        assert Path(ruta).is_file(), nombre
        red = Red.cargar(ruta)
        assert red.origen == "O" and red.destino == "T"


def test_las_modificaciones_estan_hechas_con_los_metodos_de_red():
    inicial = Red.cargar(ARCHIVO_RED)

    sin_oa = inicial.copia()
    sin_oa.desactivar_ruta("O", "A")
    con_ot = inicial.copia()
    con_ot.agregar_conexion("O", "T", 6)

    assert Red.cargar(CONFIGURACIONES["Modificación 1 (sin O → A)"]).a_dict() == sin_oa.a_dict()
    assert Red.cargar(CONFIGURACIONES["Modificación 2 (O → T, cap. 6)"]).a_dict() == con_ot.a_dict()


def test_la_tabla_comparativa_tiene_el_flujo_y_el_corte_de_cada_configuracion():
    filas = calcular_comparacion("O", "T")

    assert [fila["Configuración"] for fila in filas] == list(CONFIGURACIONES)
    assert [fila["Flujo máximo"] for fila in filas] == [25, 16, 31]
    assert [fila["Capacidad del corte"] for fila in filas] == [25, 16, 31]
    assert set(filas[0]) == {
        "Configuración",
        "Flujo máximo",
        "Capacidad del corte",
        "S",
        "T",
        "Arcos del corte",
    }

    assert filas[1]["S"] == "B, C, F, O"
    assert filas[1]["T"] == "A, D, E, G, H, I, T"
    assert filas[1]["Arcos del corte"] == "B → D, C → G, F → I"
    assert filas[2]["Arcos del corte"].endswith(", O → T")


def test_la_comparacion_usa_los_extremos_elegidos():
    filas = calcular_comparacion("A", "T")

    assert len(filas) == 3
    for fila in filas:
        assert fila["Flujo máximo"] == fila["Capacidad del corte"]
        assert "A" in [centro.strip() for centro in fila["S"].split(",")]
        assert "T" in [centro.strip() for centro in fila["T"].split(",")]


def test_la_interfaz_muestra_el_selector_y_la_tabla_comparativa():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    assert not interfaz.exception

    selector = control(interfaz, "selectbox", "Configuración")
    assert selector.value == CONFIGURACION_INICIAL
    assert selector.options == list(CONFIGURACIONES)

    tabla = interfaz.dataframe[0].value
    assert len(tabla) == 3
    assert list(tabla["Configuración"]) == list(CONFIGURACIONES)
    assert list(tabla["Flujo máximo"]) == [25, 16, 31]


def test_se_puede_cambiar_entre_configuraciones_y_recalcular():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    boton(interfaz, "Calcular flujo máximo").click().run()
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "25 paquetes/h"

    selector = control(interfaz, "selectbox", "Configuración").set_value(
        "Modificación 1 (sin O → A)"
    )
    selector.run()
    assert not interfaz.exception
    assert not interfaz.metric  # el resultado anterior ya no corresponde
    boton(interfaz, "Calcular flujo máximo").click().run()
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "16 paquetes/h"

    control(interfaz, "selectbox", "Configuración").set_value(
        "Modificación 2 (O → T, cap. 6)"
    ).run()
    boton(interfaz, "Calcular flujo máximo").click().run()
    metricas = {m.label: m.value for m in interfaz.metric}
    assert metricas["Flujo máximo"] == "31 paquetes/h"
    assert metricas["Rutas"] == "19"


def test_cambiar_de_configuracion_descarta_los_cambios_locales():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    boton(interfaz, "Desactivar").click().run()
    assert not interfaz.exception

    control(interfaz, "selectbox", "Configuración").set_value(
        "Modificación 2 (O → T, cap. 6)"
    ).run()
    boton(interfaz, "Calcular flujo máximo").click().run()

    assert not interfaz.exception
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "31 paquetes/h"


def test_restablecer_vuelve_a_la_red_inicial_y_al_selector():
    from streamlit.testing.v1 import AppTest

    interfaz = AppTest.from_file(str(RUTA_APP), default_timeout=30).run()
    control(interfaz, "selectbox", "Configuración").set_value(
        "Modificación 2 (O → T, cap. 6)"
    ).run()
    boton(interfaz, "Restablecer red inicial").click().run()

    assert not interfaz.exception
    assert control(interfaz, "selectbox", "Configuración").value == CONFIGURACION_INICIAL
    boton(interfaz, "Calcular flujo máximo").click().run()
    assert {m.label: m.value for m in interfaz.metric}["Flujo máximo"] == "25 paquetes/h"

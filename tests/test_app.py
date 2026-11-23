"""Pruebas de la interfaz (app.py) y de su conexión con los algoritmos reales."""

from pathlib import Path

import app
from src.red import Red
from app import (
    ARCHIVO_RED,
    COLOR_ARCO_CORTE,
    COLOR_DESTINO,
    COLOR_ORIGEN,
    COLOR_RUTA_SATURADA,
    COLOR_S,
    COLOR_T,
    calcular_resultado,
    construir_grafo,
    html_del_grafo,
)
from src.corte import corte_minimo
from src.flujo import edmonds_karp


def test_la_interfaz_importa_los_algoritmos_reales():
    assert app.edmonds_karp is edmonds_karp
    assert app.corte_minimo is corte_minimo
    assert edmonds_karp.__module__ == "src.flujo"
    assert corte_minimo.__module__ == "src.corte"


def test_el_resultado_de_la_interfaz_es_el_de_los_algoritmos():
    red = Red.cargar(ARCHIVO_RED)
    valor, flujo = edmonds_karp(red, "O", "T")
    _, _, arcos, capacidad = corte_minimo(red, flujo, "O")

    resultado = calcular_resultado(red, "O", "T")

    assert resultado["flujo_maximo"] == valor == 25
    assert resultado["flujo_por_arco"] == flujo
    assert resultado["corte_minimo"]["capacidad"] == capacidad == 25
    assert resultado["corte_minimo"]["arcos"] == arcos


def test_la_interfaz_usa_las_firmas_acordadas(monkeypatch):
    red = Red.cargar(ARCHIVO_RED)
    flujo = {("A", "D"): 6}
    llamadas = []

    def flujo_falso(*args):
        llamadas.append(args)
        return 6, flujo

    def corte_falso(*args):
        llamadas.append(args)
        return {"A"}, {"D"}, [("A", "D")], 6

    monkeypatch.setattr(app, "edmonds_karp", flujo_falso)
    monkeypatch.setattr(app, "corte_minimo", corte_falso)
    resultado = calcular_resultado(red, "A", "D")

    assert llamadas == [(red, "A", "D"), (red, flujo, "A")]
    assert resultado["flujo_maximo"] == 6
    assert resultado["flujo_por_arco"] == flujo
    assert resultado["corte_minimo"] == {
        "S": {"A"},
        "T": {"D"},
        "arcos": [("A", "D")],
        "capacidad": 6,
    }


def test_el_grafo_muestra_sentido_capacidad_y_extremos():
    red = Red.cargar(ARCHIVO_RED)
    grafo = construir_grafo(red, "O", "T")

    assert len(grafo.nodes) == 11
    assert len(grafo.edges) == 18
    assert next(n for n in grafo.nodes if n["id"] == "O")["color"] == COLOR_ORIGEN
    assert next(n for n in grafo.nodes if n["id"] == "T")["color"] == COLOR_DESTINO

    arco = next(e for e in grafo.edges if e["from"] == "O" and e["to"] == "A")
    assert arco["arrows"] == "to"
    assert arco["label"] == "12"
    assert "Capacidad: 12 paquetes/h" in arco["title"]


def test_el_grafo_resalta_rutas_saturadas():
    red = Red.cargar(ARCHIVO_RED)
    grafo = construir_grafo(red, "O", "T", {("O", "A"): 12, ("O", "C"): 6})

    saturada = next(e for e in grafo.edges if e["from"] == "O" and e["to"] == "A")
    assert "f=12" in saturada["label"]
    assert saturada["color"] == COLOR_RUTA_SATURADA
    libre = next(e for e in grafo.edges if e["from"] == "O" and e["to"] == "C")
    assert "f=6" in libre["label"]
    assert libre["color"] != COLOR_RUTA_SATURADA


def test_los_vertices_muestran_a_que_lado_del_corte_pertenecen():
    red = Red.cargar(ARCHIVO_RED)
    valor, flujo = edmonds_karp(red, "O", "T")
    assert valor == 25
    corte = calcular_resultado(red, "O", "T")["corte_minimo"]
    grafo = construir_grafo(red, "O", "T", flujo, corte)
    colores = {n["id"]: n["color"] for n in grafo.nodes}

    assert colores["O"] == COLOR_ORIGEN
    assert colores["T"] == COLOR_DESTINO
    assert colores["A"] == COLOR_S
    assert colores["F"] == COLOR_S
    assert colores["G"] == COLOR_T
    assert colores["H"] == COLOR_T


def test_los_arcos_del_corte_se_resaltan_en_el_dibujo():
    red = Red.cargar(ARCHIVO_RED)
    resultado = calcular_resultado(red, "O", "T")
    corte = resultado["corte_minimo"]
    grafo = construir_grafo(
        red, "O", "T", resultado["flujo_por_arco"], corte
    )
    arcos = {(e["from"], e["to"]): e for e in grafo.edges}

    for u, v in corte["arcos"]:
        assert arcos[(u, v)]["color"] == COLOR_ARCO_CORTE
        assert arcos[(u, v)]["width"] == 5
        assert "✂" in arcos[(u, v)]["label"]
        assert "Arco del corte mínimo" in arcos[(u, v)]["title"]
    assert arcos[("O", "A")]["color"] != COLOR_ARCO_CORTE


def test_las_etiquetas_no_rotan():
    grafo = construir_grafo(Red.cargar(ARCHIVO_RED), "O", "T")

    # Si rotan con la flecha, un 6 se lee como 9.
    assert grafo.options["edges"]["font"]["align"] == "horizontal"


def test_la_red_queda_fija_de_izquierda_a_derecha():
    red = Red.cargar(ARCHIVO_RED)
    grafo = construir_grafo(red, "O", "T")
    posicion = {n["id"]: (n["x"], n["y"]) for n in grafo.nodes}

    assert grafo.options["physics"]["enabled"] is False
    assert len(set(posicion.values())) == len(red.vertices)
    assert min(posicion, key=lambda v: posicion[v][0]) == "O"
    assert max(posicion, key=lambda v: posicion[v][0]) == "T"


def test_solo_se_curvan_las_rutas_que_taparia_otro_centro():
    red = Red.cargar(ARCHIVO_RED)
    assert not any("smooth" in e for e in construir_grafo(red, "O", "T").edges)

    red.agregar_conexion("O", "T", 3)
    nueva = construir_grafo(red, "O", "T").edges[-1]
    assert nueva["smooth"]["enabled"] is True


def test_el_html_del_grafo_se_puede_incrustar():
    red = Red.cargar(ARCHIVO_RED)
    html = html_del_grafo(construir_grafo(red, "O", "T"))

    assert "<html" in html.lower()
    assert "vis-network" in html
    assert "cdnjs" not in html  # el HTML es autocontenido, sin depender de internet


def test_la_interfaz_muestra_flujo_corte_y_tabla_de_rutas():
    from streamlit.testing.v1 import AppTest

    ruta = Path(app.__file__).resolve()
    interfaz = AppTest.from_file(str(ruta), default_timeout=30).run()
    assert not interfaz.exception

    interfaz.button[0].click().run()
    assert not interfaz.exception

    metricas = {m.label: m.value for m in interfaz.metric}
    assert metricas["Flujo máximo"] == "25 paquetes/h"
    assert metricas["Capacidad del corte"] == "25 paquetes/h"

    tabla = interfaz.dataframe[0].value
    assert len(tabla) == len(Red.cargar(ARCHIVO_RED).arcos())
    assert set(tabla.columns) == {"Ruta", "Flujo", "Capacidad", "Estado", "En corte"}
    assert (tabla["En corte"] == "Sí").sum() == 5

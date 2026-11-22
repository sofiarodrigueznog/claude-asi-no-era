"""Pruebas de la interfaz base (app.py)."""

import app
from src.red import Red
from app import (
    ARCHIVO_RED,
    COLOR_DESTINO,
    COLOR_ORIGEN,
    COLOR_RUTA_SATURADA,
    calcular_resultado,
    construir_grafo,
    html_del_grafo,
)


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


def test_el_html_del_grafo_se_puede_incrustar():
    red = Red.cargar(ARCHIVO_RED)
    html = html_del_grafo(construir_grafo(red, "O", "T"))

    assert "<html" in html.lower()
    assert "vis-network" in html
    assert "cdnjs" not in html  # el HTML es autocontenido, sin depender de internet

"""Pruebas de la interfaz base (app.py)."""

from src.red import Red
from app import (
    ARCHIVO_RED,
    COLOR_DESTINO,
    COLOR_ORIGEN,
    calcular_flujo_maximo,
    construir_grafo,
    html_del_grafo,
)


def test_resultado_de_prueba_para_la_red_inicial():
    red = Red.cargar(ARCHIVO_RED)
    resultado = calcular_flujo_maximo(red, "O", "T")

    assert resultado["es_prueba"] is True
    assert (resultado["origen"], resultado["destino"]) == ("O", "T")
    assert resultado["flujo_maximo"] == 25
    assert resultado["flujo_por_arco"][("O", "A")] == 11
    assert resultado["flujo_por_arco"][("H", "T")] == 10
    assert resultado["corte_minimo"]["capacidad"] == 25
    assert resultado["corte_minimo"]["arcos"] == [
        ("C", "G"),
        ("D", "H"),
        ("E", "H"),
        ("E", "I"),
        ("F", "I"),
    ]


def test_resultado_de_prueba_para_otro_par_de_centros():
    red = Red.cargar(ARCHIVO_RED)
    resultado = calcular_flujo_maximo(red, "A", "T")

    # Capacidad que sale de A (6 + 5) y que llega a T (5 + 12 + 12).
    assert resultado["flujo_maximo"] == 11
    assert resultado["flujo_por_arco"] == {}


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
    resultado = calcular_flujo_maximo(red, "O", "T")
    grafo = construir_grafo(red, "O", "T", resultado["flujo_por_arco"])

    saturada = next(e for e in grafo.edges if e["from"] == "O" and e["to"] == "A")
    assert "f=11" in saturada["label"]
    libre = next(e for e in grafo.edges if e["from"] == "O" and e["to"] == "C")
    assert "f=6" in libre["label"]


def test_el_html_del_grafo_se_puede_incrustar():
    red = Red.cargar(ARCHIVO_RED)
    html = html_del_grafo(construir_grafo(red, "O", "T"))

    assert "<html" in html.lower()
    assert "vis-network" in html
    assert "cdnjs" not in html  # el HTML es autocontenido, sin depender de internet

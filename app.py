"""
Interfaz Streamlit del simulador de una red de distribución.

Muestra la red de `data/red_inicial.json` con pyvis (centros, sentido de cada ruta y su
capacidad), permite elegir origen y destino y conecta el botón «Calcular flujo máximo»
con los algoritmos reales:

    edmonds_karp(red, s, t) -> (valor_maximo, flujo)
    corte_minimo(red, flujo, s, t) -> (S, T, arcos_corte, capacidad_corte)

Además del valor del flujo, se muestra el flujo/capacidad de cada arco (en el dibujo
y en una tabla), la partición S/T y los arcos del corte resaltados.
"""

from __future__ import annotations

from math import hypot
from pathlib import Path
from typing import Any

import streamlit as st
from pyvis.network import Network

from src.corte import corte_minimo
from src.flujo import edmonds_karp
from src.red import Red, RedInvalidaError

BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_RED = BASE_DIR / "data" / "red_inicial.json"

COLOR_ORIGEN = "#2e7d32"
COLOR_DESTINO = "#c62828"
COLOR_S = "#bbdefb"
COLOR_T = "#ffcdd2"
COLOR_CENTRO = "#90caf9"
COLOR_RUTA = "#455a64"
COLOR_RUTA_SATURADA = "#ef6c00"
COLOR_RUTA_INACTIVA = "#b0bec5"
COLOR_ARCO_CORTE = "#d32f2f"

OPCIONES_VIS = """
{
  "edges": {
    "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
    "font": {"size": 18, "align": "horizontal", "strokeWidth": 0, "background": "#ffffff"},
    "smooth": false
  },
  "layout": {"randomSeed": 1},
  "physics": {"enabled": false},
  "interaction": {"hover": true, "tooltipDelay": 120}
}
"""

# Misma disposición que la figura del informe: O a la izquierda y T a la derecha.
POSICIONES = {
    "O": (0, 0),
    "A": (180, -165),
    "B": (180, 0),
    "C": (180, 165),
    "D": (330, -220),
    "E": (480, -70),
    "F": (360, 77),
    "G": (360, 220),
    "H": (600, -143),
    "I": (600, 11),
    "T": (780, 0),
}
RADIO_CENTRO = 28


def calcular_resultado(red: Red, origen: str, destino: str) -> dict[str, Any]:
    """
    Entradas: la red validada y los centros origen y destino elegidos en la interfaz.
    Resultado: diccionario para la interfaz, armado con `edmonds_karp` y `corte_minimo`.
    """
    valor_maximo, flujo = edmonds_karp(red, origen, destino)
    lado_s, lado_t, arcos_corte, capacidad_corte = corte_minimo(
        red, flujo, origen, destino
    )
    return {
        "origen": origen,
        "destino": destino,
        "flujo_maximo": valor_maximo,
        "flujo_por_arco": flujo,
        "corte_minimo": {
            "S": lado_s,
            "T": lado_t,
            "arcos": arcos_corte,
            "capacidad": capacidad_corte,
        },
    }


def pasa_sobre_un_centro(origen: str, destino: str) -> bool:
    """
    Entradas: los extremos de una ruta.
    Resultado: True si su flecha recta pasaría por encima de otro centro; en ese caso se
    dibuja curva para que se vea (ocurre al agregar conexiones como O → T).
    """
    if origen not in POSICIONES or destino not in POSICIONES:
        return False
    (x1, y1), (x2, y2) = POSICIONES[origen], POSICIONES[destino]
    dx, dy = x2 - x1, y2 - y1
    largo = hypot(dx, dy)
    for centro, (x, y) in POSICIONES.items():
        if centro in (origen, destino):
            continue
        avance = ((x - x1) * dx + (y - y1) * dy) / largo
        distancia = abs((x - x1) * dy - (y - y1) * dx) / largo
        if 0 < avance < largo and distancia < RADIO_CENTRO:
            return True
    return False


def construir_grafo(
    red: Red,
    origen: str,
    destino: str,
    flujo_por_arco: dict[tuple[str, str], int] | None = None,
    corte: dict[str, Any] | None = None,
) -> Network:
    """
    Entradas: la red, los centros a resaltar y, opcionalmente, el flujo por ruta y
    el corte con las claves `S`, `T` y `arcos`.
    Resultado: un grafo dirigido de pyvis con la capacidad y el flujo en cada flecha.
    Los vértices se colorean según su lado del corte (salvo origen y destino, que
    conservan sus colores), los arcos del corte se resaltan en rojo, las rutas
    inactivas se dibujan discontinuas y las saturadas, en naranja.
    """
    flujo_por_arco = flujo_por_arco or {}
    lado_s = corte["S"] if corte else set()
    lado_t = corte["T"] if corte else set()
    arcos_corte = set(corte["arcos"]) if corte else set()
    grafo = Network(
        height="520px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#ffffff",
        # Incluye vis-network en el HTML: así el mapa se ve aunque el navegador no
        # tenga acceso a internet y no se crea una carpeta `lib/` en el proyecto.
        cdn_resources="in_line",
    )
    grafo.set_options(OPCIONES_VIS)

    for vertice in red.vertices:
        if vertice == origen:
            color, color_texto, titulo = COLOR_ORIGEN, "#ffffff", f"Origen: {vertice} · S"
        elif vertice == destino:
            color, color_texto, titulo = COLOR_DESTINO, "#ffffff", f"Destino: {vertice} · T"
        elif vertice in lado_s:
            color, color_texto, titulo = COLOR_S, "#263238", f"Conjunto S: {vertice}"
        elif vertice in lado_t:
            color, color_texto, titulo = COLOR_T, "#263238", f"Conjunto T: {vertice}"
        else:
            color, color_texto, titulo = COLOR_CENTRO, "#263238", f"Centro: {vertice}"
        # Un centro que no esté en POSICIONES lo ubica vis con semilla fija.
        posicion = dict(zip("xy", POSICIONES.get(vertice, ())))
        # Con "circle" el nombre va dentro del nodo y las flechas no lo tapan.
        grafo.add_node(
            vertice,
            label=vertice,
            title=titulo,
            color=color,
            shape="circle",
            font={"size": 22, "color": color_texto},
            widthConstraint=30,
            **posicion,
        )

    for arco in red.arcos():
        flujo = flujo_por_arco.get((arco.origen, arco.destino))
        es_corte = (arco.origen, arco.destino) in arcos_corte
        detalles = [f"Capacidad: {arco.capacidad} paquetes/h"]
        if not arco.activa:
            detalles.append("Ruta desactivada (capacidad efectiva 0)")
        if flujo is not None:
            detalles.append(f"Flujo: {flujo} paquetes/h")
        if es_corte:
            detalles.append("Arco del corte mínimo")

        etiqueta = str(arco.capacidad)
        if flujo is not None:
            etiqueta += f" | f={flujo}"
        if not arco.activa:
            etiqueta += " (inactiva)"
        if es_corte:
            etiqueta = "✂ " + etiqueta

        if es_corte:
            color = COLOR_ARCO_CORTE
        elif not arco.activa:
            color = COLOR_RUTA_INACTIVA
        elif flujo is not None and flujo == arco.capacidad:
            color = COLOR_RUTA_SATURADA
        else:
            color = COLOR_RUTA

        curva = {}
        if pasa_sobre_un_centro(arco.origen, arco.destino):
            curva["smooth"] = {"enabled": True, "type": "curvedCW", "roundness": 0.3}

        grafo.add_edge(
            arco.origen,
            arco.destino,
            label=etiqueta,
            title=f"{arco.origen} → {arco.destino}\n" + "\n".join(detalles),
            arrows="to",
            color=color,
            width=5 if es_corte else (3 if flujo else 2),
            dashes=not arco.activa,
            **curva,
        )

    return grafo


def html_del_grafo(grafo: Network) -> str:
    """
    Entradas: un grafo de pyvis.
    Resultado: el HTML autocontenido, listo para incrustar con `st.iframe`.
    """
    return grafo.generate_html()


def main() -> None:
    """Dibuja la interfaz: red, selectores de extremos, botón y resultado."""
    st.set_page_config(page_title="Simulador de red de flujo", page_icon="📦", layout="wide")
    st.title("📦 Simulador de una red de distribución de paquetes")
    st.caption(
        "Red inicial: `data/red_inicial.json` · las flechas indican el sentido de cada ruta "
        "y la etiqueta su capacidad en paquetes/h."
    )

    try:
        red = Red.cargar(ARCHIVO_RED)
    except (RedInvalidaError, OSError) as error:
        st.error(f"No se pudo cargar la red inicial: {error}")
        st.stop()
        return

    with st.sidebar:
        st.header("Parámetros del envío")
        origen = st.selectbox(
            "Centro de origen", red.vertices, index=red.vertices.index(red.origen)
        )
        destino = st.selectbox(
            "Centro de destino", red.vertices, index=red.vertices.index(red.destino)
        )
        extremos_validos = origen != destino
        if not extremos_validos:
            st.warning("El origen y el destino deben ser centros distintos.")
        calcular = st.button(
            "Calcular flujo máximo", type="primary", disabled=not extremos_validos
        )
        st.markdown("---")
        st.caption("Resultado calculado con Edmonds–Karp y corte mínimo reales.")

    clave = (origen, destino)
    if st.session_state.get("_clave_resultado") != clave:
        st.session_state.pop("resultado", None)
        st.session_state["_clave_resultado"] = clave

    if calcular and extremos_validos:
        try:
            st.session_state["resultado"] = calcular_resultado(red, origen, destino)
        except ValueError as error:
            st.error(f"No se pudo calcular el flujo: {error}")
    resultado = st.session_state.get("resultado")

    if resultado is not None:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Flujo máximo", f"{resultado['flujo_maximo']} paquetes/h")
        col2.metric(
            "Capacidad del corte", f"{resultado['corte_minimo']['capacidad']} paquetes/h"
        )
        col3.metric("Centros", len(red.vertices))
        col4.metric("Rutas", len(red.arcos()))

    st.subheader("Red cargada")
    st.iframe(
        html_del_grafo(
            construir_grafo(
                red,
                origen,
                destino,
                resultado["flujo_por_arco"] if resultado else None,
                resultado["corte_minimo"] if resultado else None,
            )
        ),
        height=540,
    )

    if resultado is not None:
        corte = resultado["corte_minimo"]
        arcos_corte = set(corte["arcos"])
        with st.expander("Detalle del resultado"):
            st.markdown(f"**Origen:** {resultado['origen']} · **Destino:** {resultado['destino']}")
            st.markdown(
                f"**Partición:** S = {', '.join(sorted(corte['S']))} · "
                f"T = {', '.join(sorted(corte['T']))}"
            )
            flujo = resultado["flujo_por_arco"]
            st.write("Flujo y capacidad de cada ruta:")
            st.dataframe(
                [
                    {
                        "Ruta": f"{arco.origen} → {arco.destino}",
                        "Flujo": flujo.get((arco.origen, arco.destino), 0),
                        "Capacidad": arco.capacidad,
                        "Estado": "Activa" if arco.activa else "Inactiva",
                        "En corte": "Sí" if (arco.origen, arco.destino) in arcos_corte else "",
                    }
                    for arco in red.arcos()
                ],
                width="stretch",
                hide_index=True,
            )
            rutas_corte = ", ".join(f"{u} → {v}" for u, v in corte["arcos"]) or "—"
            st.markdown(
                f"**Corte mínimo:** {corte['capacidad']} paquetes/h · "
                f"rutas: {rutas_corte}"
            )


if __name__ == "__main__":
    main()

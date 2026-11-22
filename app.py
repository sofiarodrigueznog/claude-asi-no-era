"""
Primera versión de la interfaz Streamlit del simulador de una red de distribución.

Muestra la red de `data/red_inicial.json` con pyvis (centros, sentido de cada ruta y su
capacidad), permite elegir origen y destino e incluye el botón «Calcular flujo máximo».

La interfaz usa las firmas acordadas:

    edmonds_karp(red, s, t) -> (valor_maximo, flujo)
    corte_minimo(red, flujo, s) -> (S, T, arcos_corte, capacidad_corte)

Mientras no existan `src/flujo.py` y `src/corte.py` vienen de `src/resultado_prueba.py`.
Cuando existan, solo se cambia el import por:

    from src.corte import corte_minimo
    from src.flujo import edmonds_karp
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st
from pyvis.network import Network

from src.red import Red, RedInvalidaError
from src.resultado_prueba import corte_minimo, edmonds_karp

BASE_DIR = Path(__file__).resolve().parent
ARCHIVO_RED = BASE_DIR / "data" / "red_inicial.json"
# Los avisos de "prueba" desaparecen solos al cambiar el import por el algoritmo real.
ES_PRUEBA = edmonds_karp.__module__ == "src.resultado_prueba"

COLOR_ORIGEN = "#2e7d32"
COLOR_DESTINO = "#c62828"
COLOR_CENTRO = "#90caf9"
COLOR_RUTA = "#455a64"
COLOR_RUTA_SATURADA = "#ef6c00"
COLOR_RUTA_INACTIVA = "#b0bec5"

OPCIONES_VIS = """
{
  "edges": {
    "arrows": {"to": {"enabled": true, "scaleFactor": 0.5}},
    "font": {"size": 12, "align": "top", "strokeWidth": 2, "strokeColor": "#ffffff"}
  },
  "nodes": {"shape": "dot", "font": {"size": 16}},
  "physics": {
    "solver": "forceAtlas2Based",
    "forceAtlas2Based": {
      "gravitationalConstant": -70,
      "springLength": 140,
      "springConstant": 0.06
    },
    "stabilization": {"iterations": 250}
  },
  "interaction": {"hover": true, "tooltipDelay": 120}
}
"""


def calcular_resultado(red: Red, origen: str, destino: str) -> dict[str, Any]:
    """
    Entradas: la red validada y los centros origen y destino elegidos en la interfaz.
    Resultado: diccionario para la interfaz, armado con `edmonds_karp` y `corte_minimo`.
    """
    valor_maximo, flujo = edmonds_karp(red, origen, destino)
    lado_s, lado_t, arcos_corte, capacidad_corte = corte_minimo(red, flujo, origen)
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


def construir_grafo(
    red: Red,
    origen: str,
    destino: str,
    flujo_por_arco: dict[tuple[str, str], int] | None = None,
) -> Network:
    """
    Entradas: la red, los centros a resaltar y, opcionalmente, el flujo por ruta.
    Resultado: un grafo dirigido de pyvis con la capacidad en cada flecha; las rutas
    inactivas se dibujan discontinuas y las saturadas, en otro color.
    """
    flujo_por_arco = flujo_por_arco or {}
    grafo = Network(
        height="520px",
        width="100%",
        directed=True,
        notebook=False,
        bgcolor="#ffffff",
        font_color="#263238",
        # Incluye vis-network en el HTML: así el mapa se ve aunque el navegador no
        # tenga acceso a internet y no se crea una carpeta `lib/` en el proyecto.
        cdn_resources="in_line",
    )
    grafo.set_options(OPCIONES_VIS)

    for vertice in red.vertices:
        if vertice == origen:
            color, size, titulo = COLOR_ORIGEN, 26, f"Origen: {vertice}"
        elif vertice == destino:
            color, size, titulo = COLOR_DESTINO, 26, f"Destino: {vertice}"
        else:
            color, size, titulo = COLOR_CENTRO, 18, f"Centro: {vertice}"
        grafo.add_node(vertice, label=vertice, title=titulo, color=color, size=size)

    for arco in red.arcos():
        flujo = flujo_por_arco.get((arco.origen, arco.destino))
        detalles = [f"Capacidad: {arco.capacidad} paquetes/h"]
        if not arco.activa:
            detalles.append("Ruta desactivada (capacidad efectiva 0)")
        if flujo is not None:
            detalles.append(f"Flujo: {flujo} paquetes/h")

        etiqueta = str(arco.capacidad)
        if flujo is not None:
            etiqueta += f" | f={flujo}"
        if not arco.activa:
            etiqueta += " (inactiva)"

        if not arco.activa:
            color = COLOR_RUTA_INACTIVA
        elif flujo is not None and flujo == arco.capacidad:
            color = COLOR_RUTA_SATURADA
        else:
            color = COLOR_RUTA

        grafo.add_edge(
            arco.origen,
            arco.destino,
            label=etiqueta,
            title=f"{arco.origen} → {arco.destino}\n" + "\n".join(detalles),
            arrows="to",
            color=color,
            width=3 if flujo else 2,
            dashes=not arco.activa,
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
        if ES_PRUEBA:
            st.caption("Resultado de prueba hasta que estén `src/flujo.py` y `src/corte.py`.")

    clave = (origen, destino)
    if st.session_state.get("_clave_resultado") != clave:
        st.session_state.pop("resultado", None)
        st.session_state["_clave_resultado"] = clave

    if calcular and extremos_validos:
        try:
            st.session_state["resultado"] = calcular_resultado(red, origen, destino)
        except NotImplementedError as aviso:
            st.info(str(aviso))
    resultado = st.session_state.get("resultado")

    if resultado is not None:
        col1, col2, col3 = st.columns(3)
        titulo_flujo = "Flujo máximo (prueba)" if ES_PRUEBA else "Flujo máximo"
        col1.metric(titulo_flujo, f"{resultado['flujo_maximo']} paquetes/h")
        col2.metric("Centros", len(red.vertices))
        col3.metric("Rutas", len(red.arcos()))

    st.subheader("Red cargada")
    st.iframe(
        html_del_grafo(
            construir_grafo(
                red, origen, destino, resultado["flujo_por_arco"] if resultado else None
            )
        ),
        height=540,
    )

    if resultado is not None:
        with st.expander("Detalle del resultado"):
            st.markdown(f"**Origen:** {resultado['origen']} · **Destino:** {resultado['destino']}")
            if resultado["flujo_por_arco"]:
                st.write("Flujo asignado por ruta:")
                st.dataframe(
                    [
                        {
                            "Ruta": f"{u} → {v}",
                            "Flujo": caudal,
                            "Capacidad": red.capacidad(u, v),
                        }
                        for (u, v), caudal in resultado["flujo_por_arco"].items()
                    ],
                    width="stretch",
                    hide_index=True,
                )
            corte = resultado["corte_minimo"]
            rutas_corte = ", ".join(f"{u} → {v}" for u, v in corte["arcos"]) or "—"
            st.markdown(
                f"**Corte mínimo:** {corte['capacidad']} paquetes/h · "
                f"rutas: {rutas_corte}"
            )
            if ES_PRUEBA:
                st.info("Este resultado es ilustrativo y se reemplazará por los módulos reales.")


if __name__ == "__main__":
    main()

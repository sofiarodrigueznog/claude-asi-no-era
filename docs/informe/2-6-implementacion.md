## 2.6 Implementación

El algoritmo está programado por el grupo en Python 3.12, sin bibliotecas que calculen flujos o
cortes. Solo se usan estructuras básicas del lenguaje (`dict`, `list`, `set` y `deque`). Las
bibliotecas externas se limitan a la interfaz y al dibujo de la red.

### Organización del código

| Archivo | Responsabilidad |
|:---|:---|
| `src/red.py` | Clase `Red`: carga el JSON, valida el modelo (sección 1.6) y aplica las modificaciones. |
| `src/flujo.py` | Edmonds–Karp sobre el grafo residual. |
| `src/corte.py` | Corte mínimo a partir del flujo máximo (sección 3.3). |
| `src/verificacion.py` | Comprobaciones de capacidad, conservación y valor de un flujo (sección 5). |
| `app.py` | Interfaz en Streamlit: dibujo de la red, cálculo, modificaciones y comparación. |
| `tests/` | 117 pruebas automáticas con pytest. |

Cada función lleva un comentario de documentación con sus entradas y su resultado.

### Grafo residual

El grafo residual se guarda como un diccionario de diccionarios: `residual[u][v]` es la capacidad
residual $c_f(u, v)$. La función `construir_grafo_residual` recorre las rutas activas y, por cada
arco $(u, v)$, guarda $c(u, v)$ hacia adelante y $0$ hacia atrás. Como la red no tiene arcos
recíprocos (sección 1.6), los dos sentidos nunca se mezclan en una misma entrada. Las rutas
desactivadas no se agregan, de modo que para el algoritmo simplemente no existen.

Los vecinos de cada centro quedan en el orden en que aparecen las rutas en el JSON. Por eso la BFS
recorre siempre los vecinos en el mismo orden y el resultado es reproducible.

### Pasos del algoritmo en el código

Cada paso de la sección 2.3 corresponde a una función de `src/flujo.py`:

| Paso | Función |
|:---|:---|
| Buscar con BFS el camino aumentante con menos arcos | `buscar_camino_bfs` y `reconstruir_camino` |
| Calcular el cuello de botella $c_f(P)$ | `calcular_cuello_de_botella` |
| Enviar $c_f(P)$: restar en cada arco del camino y sumar en su inverso | `aumentar_flujo` |
| Leer el flujo final $x(u, v)$ de cada ruta | `extraer_flujo` |
| Repetir hasta que no haya camino | `edmonds_karp` |

La búsqueda usa una cola (`deque`) y un diccionario de predecesores que también marca los centros
visitados. Solo avanza por arcos con capacidad residual positiva:

```python
def buscar_camino_bfs(residual, s, t):
    predecesor = {s: None}
    pendientes = deque([s])
    while pendientes:
        actual = pendientes.popleft()
        if actual == t:
            return reconstruir_camino(predecesor, t)
        for vecino, capacidad_residual in residual[actual].items():
            if capacidad_residual > 0 and vecino not in predecesor:
                predecesor[vecino] = actual
                pendientes.append(vecino)
    return None
```

La función principal repite búsqueda, cuello de botella y aumento hasta que la BFS no encuentra
camino:

```python
def edmonds_karp(red, s, t):
    residual = construir_grafo_residual(red)
    valor_maximo = 0
    camino = buscar_camino_bfs(residual, s, t)
    while camino is not None:
        cantidad = calcular_cuello_de_botella(residual, camino)
        aumentar_flujo(residual, camino, cantidad)
        valor_maximo += cantidad
        camino = buscar_camino_bfs(residual, s, t)
    return valor_maximo, extraer_flujo(red, residual)
```

En los fragmentos se omiten las anotaciones de tipo y la validación de entrada: la función rechaza
un origen o un destino que no estén en la red, o que sean el mismo centro. Al terminar,
`extraer_flujo` obtiene $x(u, v)$ de cada ruta como la capacidad residual de su arco hacia atrás,
$c_f(v, u)$, que acumula exactamente lo enviado por $(u, v)$.

Cada BFS visita cada centro y cada arco residual a lo más una vez, con costo $O(|E|)$. Como se vio
en las secciones 2.3 y 2.4, Edmonds–Karp realiza $O(|V| \cdot |E|)$ aumentos, así que esta
implementación mantiene el costo total $O(|V| \cdot |E|^2)$.

### Corte, verificación e interfaz

Con el flujo máximo, `corte_minimo` de `src/corte.py` vuelve a recorrer el grafo residual con BFS
desde el origen para obtener $S$ (sección 3.3). Si el destino quedó en $S$, el flujo no era máximo
y la función lanza un error. Si no, comprueba que la capacidad del corte sea igual al valor del
flujo antes de devolver el resultado. `src/verificacion.py` revisa por separado las restricciones de
capacidad y de conservación de cualquier flujo.

La interfaz (`app.py`) carga la red, llama a `edmonds_karp` y a `corte_minimo`, y muestra el
resultado sobre el dibujo de la red, hecho con pyvis, con los arcos del corte en rojo. Las
modificaciones se aplican con los métodos de `Red` sobre una copia, de modo que un cambio inválido
no altera la red. Las pruebas de `tests/` cubren cada módulo, el caso manual de la sección 5, las
tres configuraciones de la sección 4 y la interfaz.

### Código fuente y ejecución

El código fuente completo, los datos de las tres configuraciones y estas secciones del informe
están en el repositorio:

<https://github.com/sofiarodrigueznog/claude-asi-no-era>

Las dependencias, con las versiones probadas, están en `requirements.txt`: `streamlit` 1.67.0,
`pyvis` 0.3.2, `pandas` 3.1.1 y `pytest` 9.2.0. Para ejecutar la aplicación con Python 3.12 en
macOS o Linux:

```bash
git clone https://github.com/sofiarodrigueznog/claude-asi-no-era.git
cd claude-asi-no-era
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

La aplicación se abre en el navegador, en `http://localhost:8501`. Las pruebas se ejecutan con
`python -m pytest`. El archivo `README.md` del repositorio trae además los pasos para Windows y el
uso de cada parte de la interfaz.

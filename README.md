# Simulador de una red de distribución de paquetes

Proyecto 2 de **Teoría de Grafos (INFO1158)**. Aplicación que modela una red de centros
logísticos como un grafo dirigido con capacidades, calcula el **flujo máximo** con un
algoritmo implementado por nosotros, identifica un **corte mínimo** y permite simular
cambios en la red (desactivar rutas, cambiar capacidades y agregar conexiones).

**Entrega:** jueves 26 de noviembre de 2026 (informe PDF hasta las 23:00 y presentación de 12 minutos).

## Integrantes

| Integrante | Rol principal |
|---|---|
| Sofía Rodríguez | Coordinación, modelación de la red, verificación manual, informe |
| Paulo Villalobos | Algoritmo de flujo máximo, corte mínimo y comprobaciones |
| David Villegas | Interfaz Streamlit, simulación de modificaciones y comparación |

## Cómo trabajamos (Jira + GitHub)

Las tareas están en el Jira del proyecto (clave **TOG**). Cada ticket tiene su número: `TOG-1`, `TOG-2`, …

1. Toma tu ticket en Jira.
2. Crea la rama desde `main` con el formato **`TOG-<número>/<descripcion-en-minusculas>`**:
   ```bash
   git checkout main && git pull
   git checkout -b TOG-5/edmonds-karp
   ```
   Al subir la rama, el ticket pasa solo a **En progreso**.
3. Haz tus commits y sube la rama: `git push -u origin TOG-5/edmonds-karp`.
4. Abre un Pull Request hacia `main`. El ticket pasa solo a **En revisión** y Sofía recibe la solicitud de revisión.
5. Cuando Sofía aprueba y se fusiona el PR, el ticket pasa solo a **Completado**.

Reglas del repositorio:

- No se puede subir directo a `main`: todo entra por Pull Request con la aprobación de Sofía.
- GitHub rechaza cualquier rama que no siga el formato `TOG-<número>/<descripcion>`.
- Una revisión automática ("nombre-de-rama") vuelve a comprobar el formato en cada PR.

## Cómo ejecutar

Requiere **Python 3.12** y conexión a internet solo para instalar las dependencias. Las
versiones probadas están fijadas en `requirements.txt`.

1. Descargar el código:

   ```bash
   git clone https://github.com/sofiarodrigueznog/claude-asi-no-era.git
   cd claude-asi-no-era
   ```

2. Crear un entorno virtual e instalar las dependencias.

   macOS o Linux:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   Windows (PowerShell):

   ```powershell
   py -3.12 -m venv .venv
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

3. Abrir la aplicación:

   ```bash
   streamlit run app.py
   ```

   Se abre en el navegador, en http://localhost:8501. Para cerrarla, presionar `Ctrl+C` en la
   terminal.

4. Correr las pruebas automáticas (con el entorno activado):

   ```bash
   python -m pytest
   ```

## Uso de la aplicación

- **Parámetros del envío:** elegir el centro de origen y el de destino, y presionar
  «Calcular flujo máximo». Se muestran el valor del flujo máximo, la capacidad del corte
  mínimo, el flujo y la capacidad de cada ruta (en el dibujo y en una tabla) y la partición
  S / T, con los arcos del corte en rojo.
- **Modificaciones de la red:** desactivar o reactivar una ruta, cambiar su capacidad (entero
  de 1 a 12) o agregar una conexión nueva. Los lazos, las rutas repetidas y las recíprocas se
  rechazan con un mensaje. Después de un cambio, «Recalcular flujo» actualiza el resultado.
- **Restablecer red inicial** descarta los cambios. Las modificaciones solo viven en la sesión
  del navegador; el archivo `data/red_inicial.json` no se modifica.

## Estructura del código

```
app.py                  interfaz Streamlit: dibujo de la red, cálculo y modificaciones
src/
  red.py                clase Red: carga del JSON, validaciones del modelo y modificaciones
  flujo.py              flujo máximo con Edmonds–Karp sobre el grafo residual
  corte.py              corte mínimo a partir del grafo residual del flujo máximo
  verificacion.py       comprobaciones de capacidad, conservación y valor de un flujo
data/
  red_inicial.json      red principal (11 centros, 18 rutas)
  caso_manual.json      red pequeña del caso de comprobación manual
tests/                  pruebas automáticas (pytest), una por módulo y para la interfaz
docs/informe/           secciones del informe técnico en Markdown y sus figuras
requirements.txt        dependencias con las versiones probadas
```

Flujo de un cálculo: `app.py` carga la red con `Red.cargar`, llama a
`edmonds_karp(red, s, t)` para obtener el valor máximo y el flujo de cada ruta, y después a
`corte_minimo(red, flujo, s, t)` para obtener los conjuntos S y T, los arcos del corte y su
capacidad. Las modificaciones usan los métodos de `Red` sobre una copia, de modo que una
modificación inválida no altera la red.

Formato de una red en JSON:

```json
{
  "vertices": ["O", "A", "T"],
  "arcos": [
    {"origen": "O", "destino": "A", "capacidad": 8, "activa": true},
    {"origen": "A", "destino": "T", "capacidad": 5, "activa": true}
  ],
  "origen": "O",
  "destino": "T"
}
```

## Condiciones del enunciado

- El algoritmo de flujo máximo y sus procedimientos auxiliares son código propio.
  No se usan bibliotecas que calculen flujo o cortes (solo estructuras básicas de Python y
  bibliotecas de gráficos e interfaz).
- Las funciones principales llevan comentarios con sus entradas y resultados.
- Las fuentes académicas y técnicas consultadas se citan en el informe.

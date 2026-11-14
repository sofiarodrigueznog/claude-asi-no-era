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
   Al subir la rama, el ticket pasa solo a **En curso**.
3. Haz tus commits y sube la rama: `git push -u origin TOG-5/edmonds-karp`.
4. Abre un Pull Request hacia `main`. Sofía recibe la solicitud de revisión automáticamente.
5. Cuando Sofía aprueba y se fusiona el PR, el ticket pasa solo a **Listo**.

Reglas del repositorio:

- No se puede subir directo a `main`: todo entra por Pull Request con la aprobación de Sofía.
- GitHub rechaza cualquier rama que no siga el formato `TOG-<número>/<descripcion>`.
- Una revisión automática ("nombre-de-rama") vuelve a comprobar el formato en cada PR.

## Estructura

```
src/            modelo de la red, algoritmo de flujo máximo, corte mínimo y verificaciones
data/           redes en JSON (red inicial, modificaciones y caso de comprobación manual)
tests/          pruebas automáticas
docs/informe/   secciones del informe técnico
app.py          interfaz Streamlit
```

## Cómo ejecutar

Requiere Python 3.12.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Pruebas:

```bash
python -m pytest
```

## Condiciones del enunciado

- El algoritmo de flujo máximo y sus procedimientos auxiliares son código propio.
  No se usan bibliotecas que calculen flujo o cortes (solo estructuras básicas de Python y
  bibliotecas de gráficos e interfaz).
- Las funciones principales llevan comentarios con sus entradas y resultados.
- Las fuentes académicas y técnicas consultadas se citan en el informe.

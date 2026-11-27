"""
Une las secciones de docs/informe/ y genera docs/informe/informe.pdf.

Requiere pandoc 3 y una distribución de LaTeX con xelatex (por ejemplo TinyTeX).
Uso, desde la raíz del repositorio:

    python docs/informe/pdf/compilar.py

Cada sección conserva sus referencias en GitHub; en el PDF se reúnen todas en
referencias.md, al final, para no repetirlas.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CARPETA_PDF = Path(__file__).resolve().parent
CARPETA_INFORME = CARPETA_PDF.parent

SECCIONES = [
    "1-modelacion.md",
    "2-algoritmo.md",
    "2-6-implementacion.md",
    "3-corte-minimo.md",
    "4-simulacion.md",
    "5-verificacion.md",
    "6-conclusiones.md",
    "referencias.md",
]

# Un bloque "## Referencias" llega hasta el siguiente título de nivel 1 o 2, o el final.
REFERENCIAS_DE_SECCION = re.compile(r"^## Referencias\s*$.*?(?=^#{1,2} |\Z)", re.M | re.S)


def unir_secciones() -> str:
    """
    Entradas: ninguna; lee los archivos de SECCIONES en ese orden.
    Resultado: el Markdown completo del informe, sin las listas de referencias de
    cada sección (salvo la de referencias.md).
    """
    partes = []
    for nombre in SECCIONES:
        texto = (CARPETA_INFORME / nombre).read_text(encoding="utf-8")
        if nombre != "referencias.md":
            texto = REFERENCIAS_DE_SECCION.sub("", texto)
        partes.append(texto.strip())
    return "\n\n".join(partes) + "\n"


def compilar(salida: Path) -> None:
    """
    Entradas: ruta del PDF que se va a generar.
    Resultado: ninguno; escribe el PDF con pandoc y xelatex. Termina con error si
    pandoc falla.
    """
    with tempfile.TemporaryDirectory() as temporal:
        fuente = Path(temporal) / "informe.md"
        fuente.write_text(unir_secciones(), encoding="utf-8")
        # LaTeX corre en la carpeta temporal: las figuras se copian ahí para que las
        # rutas relativas (figuras/...) funcionen aunque la ruta del repositorio tenga espacios.
        shutil.copytree(CARPETA_INFORME / "figuras", Path(temporal) / "figuras")
        comando = [
            "pandoc",
            str(fuente),
            "--from=markdown",
            f"--metadata-file={CARPETA_PDF / 'metadatos.yaml'}",
            f"--lua-filter={CARPETA_PDF / 'filtro.lua'}",
            "--pdf-engine=xelatex",
            "--syntax-highlighting=tango",
            f"--output={salida.resolve()}",
        ]
        resultado = subprocess.run(comando, capture_output=True, text=True, cwd=temporal)
        if resultado.stderr:
            print(resultado.stderr, file=sys.stderr)
        if resultado.returncode != 0:
            sys.exit(resultado.returncode)


if __name__ == "__main__":
    destino = CARPETA_INFORME / "informe.pdf"
    compilar(destino)
    print(f"PDF generado: {destino}")

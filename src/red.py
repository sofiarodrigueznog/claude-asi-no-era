"""
Modelo de la red de distribución de paquetes.

La red es un grafo dirigido G = (V, A) con capacidades enteras:

- V: centros logísticos (vértices), identificados por su nombre.
- A: rutas (arcos) u → v con capacidad c(u, v) entre 1 y 12 paquetes por unidad de
  tiempo y un estado "activa". Una ruta desactivada sigue en la red, pero su capacidad
  efectiva es 0 (así la simulación puede cortar una ruta y volver a abrirla).
- origen s y destino t del envío.

Reglas del modelo (se revisan al cargar la red y en cada modificación):

- sin lazos (u → u),
- sin arcos repetidos (dos rutas u → v),
- sin arcos recíprocos (u → v y v → u a la vez),
- capacidades enteras entre 1 y 12,
- sin vértices aislados (todo centro participa en al menos una ruta).

Formato JSON acordado:

    {"vertices": ["O", "A", ...],
     "arcos": [{"origen": "O", "destino": "A", "capacidad": 8, "activa": true}, ...],
     "origen": "O",
     "destino": "T"}

La clave "activa" es opcional al cargar (si falta, la ruta está activa); al guardar
siempre se escribe.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

CAPACIDAD_MINIMA = 1
CAPACIDAD_MAXIMA = 12

CLAVES_RED = ("vertices", "arcos", "origen", "destino")
CLAVES_ARCO = ("origen", "destino", "capacidad")


class RedInvalidaError(ValueError):
    """
    Error de modelación de la red.

    Entradas: lista de mensajes, uno por cada problema encontrado.
    Resultado: excepción cuyo atributo `errores` conserva la lista completa, para que la
    interfaz pueda mostrar todos los problemas de una vez y no solo el primero.
    """

    def __init__(self, errores: list[str]):
        self.errores = list(errores)
        detalle = "\n".join(f"- {error}" for error in self.errores)
        super().__init__(f"La red no es válida:\n{detalle}")


@dataclass(frozen=True)
class Arco:
    """
    Ruta dirigida entre dos centros.

    Es inmutable: los cambios se hacen con los métodos de `Red`, que validan antes de
    reemplazar el arco. Así nadie puede dejar la red en un estado inválido por fuera.
    """

    origen: str
    destino: str
    capacidad: int
    activa: bool = True


# --------------------------------------------------------------------------------------
# Validaciones
# --------------------------------------------------------------------------------------


def _es_entero(valor: Any) -> bool:
    """
    Entradas: cualquier valor leído del JSON.
    Resultado: True si es un entero de verdad. Los booleanos se excluyen porque en
    Python True == 1 y no queremos aceptar "capacidad": true.
    """
    return isinstance(valor, int) and not isinstance(valor, bool)


def _error_capacidad(capacidad: Any, contexto: str) -> str | None:
    """
    Entradas: capacidad propuesta y texto que identifica la ruta en el mensaje.
    Resultado: mensaje de error, o None si la capacidad es un entero entre 1 y 12.
    """
    if not _es_entero(capacidad):
        return f"{contexto}: la capacidad debe ser un número entero (se recibió {capacidad!r})."
    if not CAPACIDAD_MINIMA <= capacidad <= CAPACIDAD_MAXIMA:
        return (
            f"{contexto}: la capacidad debe estar entre {CAPACIDAD_MINIMA} y "
            f"{CAPACIDAD_MAXIMA} (se recibió {capacidad})."
        )
    return None


def _error_ruta_nueva(
    origen: str, destino: str, existentes: set[tuple[str, str]], contexto: str
) -> str | None:
    """
    Revisa si la ruta origen → destino puede sumarse a las rutas ya existentes.

    Entradas: extremos de la ruta, conjunto de pares (u, v) ya presentes y texto que
    identifica la ruta en el mensaje. Se asume que ambos extremos son centros conocidos.
    Resultado: mensaje si la ruta es un lazo, repetida o recíproca; None si es válida.
    """
    if origen == destino:
        return f"{contexto}: es un lazo (sale y llega al mismo centro {origen})."
    if (origen, destino) in existentes:
        return f"{contexto}: la ruta {origen} → {destino} está repetida."
    if (destino, origen) in existentes:
        return (
            f"{contexto}: es recíproca de la ruta {destino} → {origen}; "
            "no se permiten rutas en ambos sentidos entre los mismos centros."
        )
    return None


def validar_datos(datos: Any) -> list[str]:
    """
    Valida una red en el formato JSON acordado, sin construirla.

    Entradas: el objeto leído del JSON (normalmente un dict).
    Resultado: lista de mensajes de error, vacía si la red es válida. Se informan
    todos los problemas encontrados, no solo el primero.
    """
    if not isinstance(datos, dict):
        return ["El archivo debe contener un objeto JSON con las claves " + ", ".join(CLAVES_RED) + "."]

    faltantes = [clave for clave in CLAVES_RED if clave not in datos]
    if faltantes:
        return ["Faltan las claves: " + ", ".join(faltantes) + "."]

    errores: list[str] = []

    # Vértices: lista de nombres de texto, sin repetir.
    vertices = datos["vertices"]
    if not isinstance(vertices, list) or not vertices:
        return ["'vertices' debe ser una lista con al menos un centro."]
    conocidos: set[str] = set()
    for nombre in vertices:
        if not isinstance(nombre, str) or not nombre.strip():
            errores.append(f"Vértice {nombre!r}: el nombre debe ser un texto no vacío.")
        elif nombre in conocidos:
            errores.append(f"Vértice {nombre}: está repetido en la lista de vértices.")
        else:
            conocidos.add(nombre)

    # Origen y destino: centros existentes y distintos.
    for clave in ("origen", "destino"):
        valor = datos[clave]
        if not isinstance(valor, str) or valor not in conocidos:
            errores.append(f"El {clave} {valor!r} no está en la lista de vértices.")
    if datos["origen"] == datos["destino"]:
        errores.append("El origen y el destino deben ser centros distintos.")

    # Arcos.
    arcos = datos["arcos"]
    if not isinstance(arcos, list):
        errores.append("'arcos' debe ser una lista de rutas.")
        return errores

    existentes: set[tuple[str, str]] = set()
    con_rutas: set[str] = set()
    for numero, arco in enumerate(arcos, start=1):
        if not isinstance(arco, dict):
            errores.append(f"Arco {numero}: debe ser un objeto con origen, destino y capacidad.")
            continue
        faltan = [clave for clave in CLAVES_ARCO if clave not in arco]
        if faltan:
            errores.append(f"Arco {numero}: faltan las claves " + ", ".join(faltan) + ".")
            continue

        u, v = arco["origen"], arco["destino"]
        contexto = f"Arco {numero} ({u} → {v})"

        desconocidos = [x for x in (u, v) if not isinstance(x, str) or x not in conocidos]
        if desconocidos:
            nombres = ", ".join(repr(x) for x in desconocidos)
            errores.append(f"{contexto}: usa centros que no están en la lista de vértices: {nombres}.")
            continue
        con_rutas.update((u, v))

        error = _error_ruta_nueva(u, v, existentes, contexto)
        if error:
            errores.append(error)
        else:
            existentes.add((u, v))

        error = _error_capacidad(arco["capacidad"], contexto)
        if error:
            errores.append(error)

        if not isinstance(arco.get("activa", True), bool):
            errores.append(f"{contexto}: 'activa' debe ser true o false.")

    # Vértices aislados: centros que no aparecen en ninguna ruta.
    for nombre in vertices:
        if isinstance(nombre, str) and nombre in conocidos and nombre not in con_rutas:
            errores.append(f"Vértice {nombre}: está aislado (no participa en ninguna ruta).")
            con_rutas.add(nombre)  # evita repetir el mensaje si el nombre vino duplicado

    return errores


# --------------------------------------------------------------------------------------
# Red
# --------------------------------------------------------------------------------------


class Red:
    """
    Red de distribución: grafo dirigido con capacidades, origen y destino.

    Se construye siempre a partir de datos validados, y cada modificación vuelve a
    comprobar las reglas del modelo, así que una `Red` existente siempre es válida.
    """

    def __init__(self, datos: dict[str, Any]):
        """
        Entradas: dict en el formato JSON acordado.
        Resultado: la red construida. Lanza RedInvalidaError con todos los problemas
        encontrados si los datos no cumplen las reglas del modelo.
        """
        errores = validar_datos(datos)
        if errores:
            raise RedInvalidaError(errores)

        self.vertices: list[str] = list(datos["vertices"])
        self.origen: str = datos["origen"]
        self.destino: str = datos["destino"]
        # dict conserva el orden de inserción: al guardar, las rutas salen en el mismo
        # orden en que se cargaron (y las nuevas, al final).
        self._arcos: dict[tuple[str, str], Arco] = {}
        for arco in datos["arcos"]:
            u, v = arco["origen"], arco["destino"]
            self._arcos[(u, v)] = Arco(u, v, arco["capacidad"], arco.get("activa", True))

    # ---- carga y guardado ------------------------------------------------------------

    @classmethod
    def desde_json(cls, texto: str | bytes) -> Red:
        """
        Entradas: contenido de un archivo JSON (texto o bytes, como los entrega el
        cargador de archivos de Streamlit).
        Resultado: la red. Lanza RedInvalidaError si el JSON está mal escrito o la red
        no cumple las reglas del modelo.
        """
        if isinstance(texto, bytes):
            texto = texto.decode("utf-8")
        try:
            datos = json.loads(texto)
        except json.JSONDecodeError as error:
            raise RedInvalidaError(
                [f"El archivo no es JSON válido (línea {error.lineno}, columna {error.colno}): {error.msg}."]
            ) from error
        return cls(datos)

    @classmethod
    def cargar(cls, ruta: str | Path) -> Red:
        """
        Entradas: ruta de un archivo JSON con la red.
        Resultado: la red. Lanza RedInvalidaError si el contenido no es válido.
        """
        return cls.desde_json(Path(ruta).read_text(encoding="utf-8"))

    def a_dict(self) -> dict[str, Any]:
        """
        Entradas: ninguna.
        Resultado: la red en el formato JSON acordado (dict nuevo, independiente de la red).
        """
        return {
            "vertices": list(self.vertices),
            "arcos": [asdict(arco) for arco in self._arcos.values()],
            "origen": self.origen,
            "destino": self.destino,
        }

    def a_json(self) -> str:
        """
        Entradas: ninguna.
        Resultado: texto JSON con el mismo estilo que data/red_inicial.json (una ruta por
        línea), para que los archivos guardados se puedan leer y comparar en un diff.
        """
        def compacto(valor: Any) -> str:
            return json.dumps(valor, ensure_ascii=False)

        datos = self.a_dict()
        rutas = ",\n".join(f"    {compacto(arco)}" for arco in datos["arcos"])
        return (
            "{\n"
            f'  "vertices": {compacto(datos["vertices"])},\n'
            f'  "arcos": [\n{rutas}\n  ],\n'
            f'  "origen": {compacto(datos["origen"])},\n'
            f'  "destino": {compacto(datos["destino"])}\n'
            "}\n"
        )

    def guardar(self, ruta: str | Path) -> None:
        """
        Entradas: ruta del archivo donde se guarda la red (se sobrescribe si existe).
        Resultado: ninguno; escribe el JSON en UTF-8.
        """
        Path(ruta).write_text(self.a_json(), encoding="utf-8")

    def copia(self) -> Red:
        """
        Entradas: ninguna.
        Resultado: una red nueva e independiente, para simular cambios sin tocar la original.
        """
        return Red(self.a_dict())

    # ---- consultas -------------------------------------------------------------------

    def arcos(self, solo_activos: bool = False) -> list[Arco]:
        """
        Entradas: solo_activos=True para omitir las rutas desactivadas.
        Resultado: lista de arcos en el orden de la red (los arcos son inmutables).
        """
        return [a for a in self._arcos.values() if a.activa or not solo_activos]

    def arco(self, origen: str, destino: str) -> Arco:
        """
        Entradas: extremos de una ruta.
        Resultado: el arco origen → destino. Lanza RedInvalidaError si no existe.
        """
        try:
            return self._arcos[(origen, destino)]
        except KeyError:
            raise RedInvalidaError([f"No existe la ruta {origen} → {destino}."]) from None

    def existe_ruta(self, origen: str, destino: str) -> bool:
        """
        Entradas: extremos de una ruta.
        Resultado: True si la ruta origen → destino está en la red (activa o no).
        """
        return (origen, destino) in self._arcos

    def capacidad(self, origen: str, destino: str) -> int:
        """
        Capacidad efectiva c(u, v) que usa el algoritmo de flujo máximo.

        Entradas: extremos de una ruta.
        Resultado: la capacidad si la ruta existe y está activa; 0 si no existe o está
        desactivada (en flujo máximo, "sin arco" equivale a capacidad 0).
        """
        arco = self._arcos.get((origen, destino))
        return arco.capacidad if arco is not None and arco.activa else 0

    def sucesores(self, centro: str) -> list[str]:
        """
        Entradas: nombre de un centro.
        Resultado: centros a los que llega una ruta activa desde `centro`.
        """
        self._exigir_centro(centro)
        return [v for (u, v), a in self._arcos.items() if u == centro and a.activa]

    def predecesores(self, centro: str) -> list[str]:
        """
        Entradas: nombre de un centro.
        Resultado: centros desde los que sale una ruta activa hacia `centro`.
        """
        self._exigir_centro(centro)
        return [u for (u, v), a in self._arcos.items() if v == centro and a.activa]

    # ---- modificaciones (simulación) -------------------------------------------------

    def desactivar_ruta(self, origen: str, destino: str) -> None:
        """
        Entradas: extremos de una ruta existente.
        Resultado: ninguno; la ruta queda inactiva (capacidad efectiva 0) pero se
        conserva en la red para poder reactivarla. Lanza RedInvalidaError si no existe.
        """
        self._arcos[(origen, destino)] = replace(self.arco(origen, destino), activa=False)

    def activar_ruta(self, origen: str, destino: str) -> None:
        """
        Entradas: extremos de una ruta existente.
        Resultado: ninguno; la ruta vuelve a estar activa. Lanza RedInvalidaError si no existe.
        """
        self._arcos[(origen, destino)] = replace(self.arco(origen, destino), activa=True)

    def cambiar_capacidad(self, origen: str, destino: str, capacidad: int) -> None:
        """
        Entradas: extremos de una ruta existente y su nueva capacidad (entero de 1 a 12).
        Resultado: ninguno; actualiza la capacidad. Lanza RedInvalidaError si la ruta no
        existe o la capacidad está fuera de rango; en ese caso la red no cambia.
        """
        arco = self.arco(origen, destino)
        error = _error_capacidad(capacidad, f"Ruta {origen} → {destino}")
        if error:
            raise RedInvalidaError([error])
        self._arcos[(origen, destino)] = replace(arco, capacidad=capacidad)

    def agregar_conexion(self, origen: str, destino: str, capacidad: int) -> None:
        """
        Entradas: dos centros existentes y la capacidad de la nueva ruta (entero de 1 a 12).
        Resultado: ninguno; agrega la ruta activa origen → destino. Lanza RedInvalidaError
        si algún centro no existe o si la ruta sería un lazo, repetida, recíproca o con
        capacidad fuera de rango; en ese caso la red no cambia.
        """
        self._exigir_centro(origen)
        self._exigir_centro(destino)
        contexto = f"Ruta {origen} → {destino}"
        errores = [
            error
            for error in (
                _error_ruta_nueva(origen, destino, set(self._arcos), contexto),
                _error_capacidad(capacidad, contexto),
            )
            if error
        ]
        if errores:
            raise RedInvalidaError(errores)
        self._arcos[(origen, destino)] = Arco(origen, destino, capacidad)

    # ---- auxiliares ------------------------------------------------------------------

    def _exigir_centro(self, centro: str) -> None:
        """
        Entradas: nombre de un centro.
        Resultado: ninguno; lanza RedInvalidaError si el centro no está en la red.
        """
        if centro not in self.vertices:
            raise RedInvalidaError([f"El centro {centro!r} no está en la red."])

    def __repr__(self) -> str:
        activas = len(self.arcos(solo_activos=True))
        return (
            f"Red({len(self.vertices)} centros, {len(self._arcos)} rutas "
            f"({activas} activas), {self.origen} → {self.destino})"
        )

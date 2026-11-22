# 2. Algoritmo de flujo máximo

El objetivo es calcular cuántos paquetes por hora pueden llegar como máximo desde el origen $O$
hasta el destino $T$, respetando la capacidad de cada ruta. En esta sección se describen dos
estrategias para resolverlo: el método de **Ford–Fulkerson** buscando caminos en profundidad (DFS)
y el algoritmo de **Edmonds–Karp**, que busca caminos en anchura (BFS). Al final se justifica cuál
se utiliza en la aplicación.

Conviene aclarar desde el inicio que no son dos ideas independientes. Ford–Fulkerson es un
**método general**: dice qué hacer en cada paso, pero no dice cómo encontrar el camino. Edmonds–Karp
es una **variante** de ese método que fija una regla concreta para elegir el camino. Por eso
comparten casi toda la explicación y se diferencian en un solo punto.

## 2.1 Conceptos base

### Flujo

Un flujo es una función $x : E \to \mathbb{R}_{\ge 0}$ que indica cuántos paquetes por hora se
envían por cada ruta. Para ser válido debe cumplir dos condiciones:

- **Capacidad:** $0 \le x(u, v) \le c(u, v)$ para todo arco $(u, v) \in E$.
- **Conservación:** en todo vértice distinto de $O$ y $T$, lo que entra es igual a lo que sale.
  Un centro intermedio no produce ni acumula paquetes.

El valor del flujo, $|x|$, es la cantidad neta que sale de $O$ (que es igual a la neta que llega a
$T$). Se denota $f^*$ a un flujo máximo y $|f^*|$ a su valor. El subíndice $f$ en $c_f$ y $G_f$ se
refiere al flujo actual $x$.

### Grafo residual

La idea del grafo residual es representar, para el flujo actual, **qué cambios todavía se pueden
hacer**. Para cada arco $(u, v) \in E$ con flujo $x(u, v)$ se definen dos capacidades residuales:

$$
c_f(u, v) = c(u, v) - x(u, v), \qquad c_f(v, u) = x(u, v).
$$

La primera indica cuántos paquetes más caben en la ruta. La segunda corresponde a un **arco
inverso** y representa la posibilidad de deshacer flujo ya enviado. Este arco inverso no es una ruta
real de la empresa: no significa que los camiones viajen de $v$ a $u$, sino que el algoritmo puede
redirigir paquetes que antes había mandado por $(u, v)$. El grafo residual $G_f$ contiene solamente
los arcos con capacidad residual mayor que cero.

El arco inverso es lo que permite corregir decisiones. Sin él, un mal camino elegido al principio
podría bloquear la solución óptima.

### Camino aumentante y cuello de botella

Un **camino aumentante** es un camino simple de $O$ a $T$ dentro del grafo residual $G_f$. Si existe,
todavía se pueden enviar más paquetes.

¿Cuántos más? Tantos como permita el arco más restringido del camino. Esa cantidad es el **cuello de
botella**:

$$
c_f(P) = \min_{(u, v) \in P} c_f(u, v).
$$

Por ejemplo, si un camino pasa por arcos residuales con capacidades 12, 6 y 7, solo se pueden
agregar 6 paquetes por hora, porque el segundo arco no admite más.

## 2.2 Método de Ford–Fulkerson (con DFS)

Ford y Fulkerson (1956) propusieron el siguiente procedimiento:

1. Comenzar con flujo cero en todas las rutas.
2. Buscar un camino aumentante de $O$ a $T$ en el grafo residual.
3. Si no existe, terminar: el flujo actual es máximo.
4. Si existe, calcular su cuello de botella $c_f(P)$.
5. Aumentar el flujo en $c_f(P)$ a lo largo del camino. En un arco original se suma; si el camino
   usa un arco inverso, se resta del arco original correspondiente.
6. Actualizar el grafo residual y volver al paso 2.

Que el resultado sea realmente el máximo lo garantiza el **teorema de flujo máximo y corte mínimo**:
cuando no queda ningún camino aumentante, el conjunto de vértices alcanzables desde $O$ en $G_f$
define un corte cuya capacidad es igual al valor del flujo, y ningún flujo puede superar la capacidad
de un corte (Cormen et al., 2009, sec. 26.2).

El método no indica cómo buscar el camino del paso 2. La versión habitual usa **búsqueda en
profundidad (DFS)**: desde $O$ se avanza por el primer arco disponible y se sigue avanzando mientras
se pueda, retrocediendo solo cuando se llega a un punto sin salida. Se queda con el primer camino que
llegue a $T$, sin importar si es largo o si su cuello de botella es pequeño.

## 2.3 Algoritmo de Edmonds–Karp (con BFS)

Edmonds y Karp (1972) mantuvieron exactamente el mismo procedimiento y cambiaron solo el paso 2:
el camino aumentante se busca con **búsqueda en anchura (BFS)**. BFS explora primero todos los
vértices a un arco de distancia de $O$, después los que están a dos arcos, y así sucesivamente. De
esta manera, el camino encontrado es siempre uno con la **menor cantidad de arcos** en el grafo
residual.

Esta regla parece un detalle, pero tiene una consecuencia importante. A medida que el algoritmo
avanza, la distancia (en número de arcos) desde $O$ hasta cada vértice del grafo residual nunca
disminuye. Además, cada vez que un arco es el cuello de botella de un camino, desaparece del grafo
residual, y para volver a ser cuello de botella la distancia de su vértice inicial tiene que haber
crecido al menos en 2. Como una distancia no puede superar $|V|$, cada arco puede ser cuello de
botella a lo más unas $|V|/2$ veces. Esto acota el número total de iteraciones por $O(|V| \cdot |E|)$,
**sin depender de las capacidades** (Cormen et al., 2009, sec. 26.2).

## 2.4 Comparación

| Aspecto | Ford–Fulkerson (DFS) | Edmonds–Karp (BFS) |
|:---|:---|:---|
| Elección del camino | El primero que encuentra DFS; puede ser largo y con cuello de botella pequeño. | El de menos arcos en el grafo residual. |
| Costo de cada iteración | $O(\lvert E \rvert)$ | $O(\lvert E \rvert)$ |
| Número de iteraciones | A lo más $\lvert f^* \rvert$, con capacidades enteras. | $O(\lvert V \rvert \cdot \lvert E \rvert)$ |
| Complejidad total | $O(\lvert E \rvert \cdot \lvert f^* \rvert)$ | $O(\lvert V \rvert \cdot \lvert E \rvert^2)$ |
| Depende de las capacidades | Sí | No |
| Terminación | Garantizada con capacidades enteras o racionales; con irracionales puede no terminar. | Garantizada siempre. |

### Complejidad

En Ford–Fulkerson, si las capacidades son enteras, cada camino aumenta el flujo en al menos 1. Por
lo tanto hay como máximo $|f^*|$ iteraciones, y cada búsqueda DFS recorre el grafo en $O(|E|)$. Así
se obtiene $O(|E| \cdot |f^*|)$.

El problema aparece cuando el flujo máximo es grande. El ejemplo clásico (Cormen et al., 2009,
fig. 26.7) es una red de cuatro vértices con dos rutas de capacidad $10^6$ conectadas por un arco
de capacidad 1. Si DFS elige siempre un camino que pasa por ese arco central, cada iteración aumenta
el flujo en solo 1 y se necesitan dos millones de iteraciones, aunque bastarían dos.

En Edmonds–Karp hay $O(|V| \cdot |E|)$ iteraciones, cada una de costo $O(|E|)$, lo que da
$O(|V| \cdot |E|^2)$. Esta cota no cambia aunque las capacidades sean muy grandes.

### Terminación

Ford–Fulkerson termina cuando las capacidades son enteras, porque el flujo crece al menos 1 en cada
paso y está acotado por $|f^*|$. Con capacidades irracionales puede elegir una secuencia infinita de
caminos cuyo aumento se hace cada vez más pequeño, e incluso converger a un valor que no es el
máximo (Cormen et al., 2009, sec. 26.2). Edmonds–Karp termina en todos los casos, porque su número
de iteraciones depende solo de $|V|$ y $|E|$.

### Aplicación a nuestra red

Con la red de la sección 1 ($|V| = 11$, $|E| = 18$), el flujo máximo no puede superar lo que sale
del origen ($12 + 10 + 9 = 31$) ni lo que llega al destino ($5 + 12 + 12 = 29$). Por lo tanto,
$|f^*| \le \min(31, 29) = 29$ y las cotas quedan:

- Ford–Fulkerson: $|E| \cdot |f^*| \le 18 \cdot 29 = 522$.
- Edmonds–Karp: $|V| \cdot |E|^2 = 11 \cdot 18^2 = 3564$.

Para esta red en particular la cota de Ford–Fulkerson es menor. Sin embargo, ambas son cotas del
peor caso y en una red de este tamaño los dos algoritmos terminan prácticamente al instante. La
diferencia que importa no es la velocidad con esta configuración, sino cómo se comportan cuando la
red cambia.

## 2.5 Justificación de la elección

Se elige **Edmonds–Karp** por las siguientes razones:

1. **Comportamiento predecible.** La aplicación permite modificar la red (agregar rutas o cambiar
   capacidades). Con Edmonds–Karp el número de iteraciones depende solo del tamaño del grafo, así que
   un cambio en las capacidades no puede disparar el tiempo de ejecución.
2. **Terminación garantizada.** No depende de que las capacidades sean enteras. Aunque en este
   proyecto lo son, el algoritmo queda correcto incluso si esa condición cambiara.
3. **Caminos fáciles de seguir.** En cada iteración BFS entrega un camino aumentante con la menor
   cantidad de arcos, lo que facilita mostrar el paso a paso en el informe y comparar los resultados
   con cálculos a mano. Si hay varios con esa cantidad, el elegido depende del orden en que se
   recorren los vecinos.
4. **Misma implementación base.** Al ser una variante de Ford–Fulkerson, se conserva toda la lógica
   del grafo residual, del cuello de botella y de la actualización del flujo. Solo cambia la búsqueda
   del camino, que con BFS además es fácil de implementar con una cola.

La desventaja es que en redes pequeñas con flujos bajos, como la nuestra, su cota teórica es mayor
que la de Ford–Fulkerson. Como esa diferencia no se nota en la práctica para este tamaño, se prioriza
la garantía de terminación y la estabilidad frente a cambios en la red.

## Referencias

- Cormen, T. H., Leiserson, C. E., Rivest, R. L. y Stein, C. (2009). *Introduction to Algorithms*
  (3.ª ed.), cap. 26 "Maximum Flow". MIT Press.
- Edmonds, J. y Karp, R. M. (1972). Theoretical improvements in algorithmic efficiency for network
  flow problems. *Journal of the ACM*, 19(2), 248–264.
- Ford, L. R. y Fulkerson, D. R. (1956). Maximal flow through a network. *Canadian Journal of
  Mathematics*, 8, 399–404.

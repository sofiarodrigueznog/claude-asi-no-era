# 3. Corte mínimo

El flujo máximo indica cuántos paquetes por hora pueden llegar de $O$ a $T$. El corte mínimo
explica **por qué** no pueden llegar más: identifica el conjunto de rutas que limita toda la red.
En esta sección se definen el corte y su capacidad, se enuncia el teorema que los relaciona con el
flujo máximo y se describe cómo la aplicación obtiene el corte a partir del resultado de
Edmonds–Karp.

## 3.1 Partición y capacidad de un corte

Un **corte** $s\text{-}t$ es una partición del conjunto de vértices en dos partes:

$$
V = S \cup (V \setminus S), \qquad S \cap (V \setminus S) = \varnothing, \qquad s \in S, \quad t \in V \setminus S.
$$

$S$ es el lado del origen y $V \setminus S$ el lado del destino. Como en la sección 5, se escribe
$V \setminus S$ en lugar de $T$ para no confundir este conjunto con el vértice $T$.

La **capacidad del corte** es la suma de las capacidades de los arcos que van de $S$ hacia
$V \setminus S$:

$$
c(S, V \setminus S) = \sum_{(u, v) \in E,\ u \in S,\ v \notin S} c(u, v).
$$

Los arcos que van en sentido contrario, de $V \setminus S$ hacia $S$, no se suman. Si se eliminan
de la red todos los arcos de $S$ hacia $V \setminus S$, no queda ningún camino dirigido de $s$ a
$t$. Por eso todo paquete que llega al destino tiene que cruzar alguno de ellos.

Un **corte mínimo** es un corte $s\text{-}t$ de capacidad mínima entre todos los posibles. Puede haber
más de uno con la misma capacidad.

## 3.2 Teorema de flujo máximo–corte mínimo

> **Teorema** (Ford y Fulkerson, 1956; Cormen et al., 2009, teorema 26.6). Sea $x$ un flujo en una
> red $G = (V, E)$ con origen $s$ y destino $t$. Las siguientes afirmaciones son equivalentes:
>
> 1. $x$ es un flujo máximo.
> 2. El grafo residual $G_f$ no contiene caminos aumentantes de $s$ a $t$.
> 3. $|x| = c(S, V \setminus S)$ para algún corte $s\text{-}t$.

La parte fácil del teorema es que **ningún flujo supera la capacidad de ningún corte**: para todo
flujo factible $x$ y todo corte $s\text{-}t$ se cumple $|x| \le c(S, V \setminus S)$ (Cormen et al.,
2009, corolario 26.5). La razón es que todo el flujo neto que sale de $s$ tiene que cruzar el corte,
y en cada arco que lo cruza no puede pasar más que su capacidad. La demostración completa de esta
desigualdad está en la sección 5.5.

La parte importante es que la igualdad siempre se alcanza: el valor del flujo máximo es igual a la
capacidad del corte mínimo,

$$
\max_{x} |x| = \min_{S} c(S, V \setminus S).
$$

Esto tiene dos consecuencias para el proyecto. La primera es que, si se encuentra un flujo y un
corte con el mismo valor, ambos son óptimos y no hace falta revisar los demás cortes. La segunda es
que el corte mínimo señala el **cuello de botella de la red**: para aumentar el flujo máximo es
necesario aumentar la capacidad de alguno de sus arcos. Mejorar una ruta que no está en el corte no
cambia el resultado.

## 3.3 Cómo el código obtiene el corte

La demostración del teorema es constructiva: cuando Edmonds–Karp termina, el grafo residual entrega
directamente un corte mínimo. La función `corte_minimo(red, flujo, s, t)` de `src/corte.py` sigue esos
pasos:

1. **Construir el grafo residual del flujo final.** Para cada ruta activa $(u, v)$ se agrega el
   arco hacia adelante con capacidad $c(u, v) - x(u, v)$ y el arco inverso con capacidad $x(u, v)$,
   igual que en la sección 2.1.
2. **Buscar los vértices alcanzables desde $s$.** Se hace una BFS desde $s$ que solo avanza por
   arcos con capacidad residual positiva. El conjunto de vértices visitados es $S$, y el resto de
   los centros forma $V \setminus S$.
3. **Listar los arcos del corte.** Son las rutas activas $(u, v)$ con $u \in S$ y $v \notin S$. Las
   rutas desactivadas en la simulación tienen capacidad 0, así que no forman parte del corte.
4. **Calcular la capacidad** sumando $c(u, v)$ sobre esos arcos.
5. **Comprobar el teorema.** La función compara la capacidad del corte con el valor del flujo
   (lo que sale de $s$ menos lo que entra a $s$) y revisa que $t$ no haya quedado en $S$. Si algo
   falla, el flujo recibido no era máximo y la función lanza un error en vez de mostrar un corte
   incorrecto.

¿Por qué el conjunto alcanzable define un corte mínimo? Como el flujo es máximo, $t$ no es
alcanzable, de modo que $t \notin S$ y la partición es un corte $s\text{-}t$. Además, todo arco original
de $S$ hacia $V \setminus S$ está saturado, porque si le quedara capacidad residual su extremo final
también sería alcanzable. Por la misma razón, todo arco de $V \setminus S$ hacia $S$ lleva flujo 0,
porque si no, su arco inverso permitiría llegar a su vértice inicial. Entonces el flujo neto que
cruza el corte es exactamente su capacidad, y por la desigualdad de la sección 3.2 ese corte es
mínimo.

La búsqueda recorre cada vértice y cada arco residual una vez, así que su costo es $O(|V| + |E|)$,
mucho menor que el del cálculo del flujo.

## 3.4 Resultado en la red inicial

Con la red de la sección 1, Edmonds–Karp entrega un flujo máximo de **25 paquetes por hora**. Al
terminar, la BFS sobre el grafo residual alcanza siete centros:

$$
S = \lbrace O,\ A,\ B,\ C,\ D,\ E,\ F\rbrace, \qquad V \setminus S = \lbrace G,\ H,\ I,\ T\rbrace.
$$

Los arcos que van de $S$ hacia $V \setminus S$ son cinco, y todos quedan saturados con el flujo
máximo:

| Arco $(u, v)$ | $c(u, v)$ | $x(u, v)$ |
|:---:|:---:|:---:|
| $(C, G)$ | 6 | 6 |
| $(D, H)$ | 7 | 7 |
| $(E, H)$ | 3 | 3 |
| $(E, I)$ | 3 | 3 |
| $(F, I)$ | 6 | 6 |

La capacidad del corte es

$$
c(S, V \setminus S) = c(C,G) + c(D,H) + c(E,H) + c(E,I) + c(F,I) = 6 + 7 + 3 + 3 + 6 = 25,
$$

igual al flujo máximo, como asegura el teorema. Además, ningún arco de la red va de
$V \setminus S$ hacia $S$, así que no hay flujo que vuelva a cruzar el corte.

El resultado muestra dónde está la restricción. Desde el origen podrían salir hasta
$12 + 10 + 9 = 31$ paquetes por hora y al destino podrían llegar hasta $5 + 12 + 12 = 29$, pero
ninguno de esos dos límites es el que manda. El cuello de botella está en las rutas que van de los
centros de transferencia $D$, $E$ y $F$ a los de consolidación $H$ e $I$, junto con la ruta
$C \to G$ que abastece al centro de transferencia $G$. En esta red además es el único corte mínimo, así que para que transporte más de 25 paquetes por hora basta con
ampliar alguna de esas cinco rutas o agregar una conexión nueva de $S$ hacia $V \setminus S$.

## Referencias

- Cormen, T. H., Leiserson, C. E., Rivest, R. L. y Stein, C. (2009). *Introduction to Algorithms*
  (3.ª ed.), cap. 26 "Maximum Flow", sec. 26.2. MIT Press.
- Ford, L. R. y Fulkerson, D. R. (1956). Maximal flow through a network. *Canadian Journal of
  Mathematics*, 8, 399–404.

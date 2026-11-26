# 6. Conclusiones

La red de distribución se modeló como una red de flujo $G = (V, E)$ con 11 centros, 18 rutas
dirigidas y capacidades enteras entre 1 y 12, con $s = O$ y $t = T$. Para resolverla se compararon
Ford–Fulkerson con DFS y Edmonds–Karp. Se eligió Edmonds–Karp porque su número de iteraciones no
depende de las capacidades, algo que importa en una aplicación donde el usuario puede cambiarlas.
El algoritmo, el corte mínimo y las comprobaciones son código propio, sin bibliotecas de flujo.

En la red inicial el flujo máximo es de **25 paquetes por hora**. Ese valor no lo fijan el origen
ni el destino, que podrían despachar 31 y recibir 29, sino un corte de cinco rutas intermedias:
$C \to G$, $D \to H$, $E \to H$, $E \to I$ y $F \to I$. Es el único corte mínimo de la red, así que
ampliar cualquier otra ruta no aumenta el resultado.

Las dos modificaciones muestran que el cuello de botella depende de la estructura completa de la
red. Al quitar $O \to A$ el flujo baja a 16 y aparece un corte distinto. Al agregar $O \to T$ sube a
31 y el corte conserva la misma partición, con un arco más. En las tres configuraciones el flujo
máximo coincide con la capacidad del corte mínimo, como establece el teorema de Ford y Fulkerson.

Los resultados se contrastaron de tres maneras. Primero, una red pequeña resuelta a mano dio los
mismos caminos, flujos y corte que el código. Segundo, las comprobaciones de capacidad, conservación
y valor se aplicaron a cada resultado. Tercero, 117 pruebas automáticas fijan los valores de las tres
configuraciones. Con esto el simulador permite estudiar qué rutas conviene ampliar o agregar antes
de modificar la red real.

# BEAR GAME — Beer Game de logística

## Propósito
Simulación multijugador del Beer Distribution Game (MIT/Sterman): 4 roles en cadena
(Minorista → Mayorista → Distribuidor → Fábrica) deciden cuánto pedir cada ronda para
minimizar el costo total (inventario ocioso + pedidos atrasados). Fenómeno central a
mostrar: el efecto bullwhip (amplificación de la variabilidad río arriba).

Los 4 jugadores humanos jugarán desde **4 ubicaciones distintas** (cada quien desde su
casa), no en la misma red local.

## Historia reciente
Hubo un primer intento en Godot/GDScript + ENet + servicio ML en FastAPI que resultó
demasiado complejo (WSL sin GUI funcional, launcher multi-proceso en PowerShell) y no
funcionaba bien. Se abandonó por completo (carpeta borrada el 2026-07-06) y se reinició
con un plan por fases, más simple: Python puro + Streamlit.

## Stack
- Python 3 (probado en WSL Ubuntu-22.04, python3 del sistema)
- Streamlit para la interfaz (aún no implementada — próxima fase)
- Sin dependencias externas por ahora (motor usa solo stdlib)
- Despliegue planeado: Streamlit Community Cloud (porque los jugadores están en
  ubicaciones distintas y necesitan una URL pública compartida)

## Estructura de archivos
```
game/
  __init__.py
  player.py       -> clase Player: inventario, backlog, fulfill(), compute_cost()
  game_state.py   -> clase GameState: pipelines de pedidos/despachos, start_round()/complete_round()
  policies.py     -> políticas de pedido automáticas (solo para pruebas en consola, sin humanos)
console_test.py   -> corre N rondas en consola con una política automática y exporta CSV
resultados_ronda.csv -> output de la última corrida de prueba
```

## Arquitectura del motor
Cadena: Cliente → Minorista → Mayorista → Distribuidor → Fábrica → (producción, ilimitada).

Cada ronda se juega en dos pasos (para que una UI pueda mostrar la demanda antes de
pedir la decisión del jugador):
1. `GameState.start_round()`: hace llegar los despachos en tránsito, calcula la demanda
   que recibe cada rol (cliente real para Minorista, pedido del rol de abajo para los
   demás) y la devuelve.
2. `GameState.complete_round(orders)`: aplica los pedidos decididos (dict rol → cantidad),
   los mete en el pipeline hacia el proveedor, despacha lo que se puede (`Player.fulfill`),
   actualiza inventario/backlog y calcula costos (`Player.compute_cost`).

Costos: inventario * 0.5 + backlog * 1.0, por ronda, por jugador.
Retrasos (lead times): 2 rondas de pedido + 2 rondas de despacho (configurable en
`GameState.__init__`).

## Validado hasta ahora
- Política ingenua (pedir = demanda recibida): consistente, muestra backlog creciente
  que nunca se recupera tras un salto de demanda (4→8 en ronda 5). Costo total: 424.
- Política nivel-objetivo simple (sin descontar pipeline): diverge fuerte (costo total:
  9,324) porque re-pide el mismo faltante varias veces mientras el pedido anterior
  sigue en camino — efecto bullwhip amplificado. Comportamiento esperado, no es bug.

## Plan por fases (definido por el usuario, ver infografía)
1. ✅ Definir MVP (4 jugadores, 20 rondas, sin ML)
2. ✅ Diseñar lógica (roles, flujo, reglas, costos)
3. ✅ Motor base en Python (Player, GameState)
4. ✅ Probar en consola
5. ✅ Guardar datos: CSV al final de la partida es suficiente. **Decisión (2026-07-06):
   no se usará SQLite.** El usuario confirmó que cada partida es autocontenida (20
   rondas y listo, sin "continuar" entre partidas como un RPG) — no hace falta
   persistencia histórica entre partidas, solo el resultado de la partida actual.
6. ✅ Interfaz Streamlit (`app.py`): selección de rol (bloqueado si ya está tomado),
   métricas de ronda/inventario/backlog, input de pedido, estado "esperando a los
   demás", avance automático de ronda cuando los 4 confirman, pantalla de resultados
   finales al llegar a la ronda 20. Estado compartido vía `st.cache_resource` +
   `threading.Lock` (una sola instancia de `GameState` para todas las sesiones).
   **Probado (2026-07-06) simulando 4 sesiones de navegador distintas** (recargando
   la página, que crea una sesión Streamlit nueva cada vez): los 4 roles se
   bloquearon correctamente al elegirse, cada sesión vio el estado compartido
   actualizado en tiempo real, y la ronda avanzó sola (1/20 → 2/20) al completarse
   los 4 pedidos. **Repo en GitHub (2026-07-07): https://github.com/Dackarl/beer-game**
   (público, rama `master`). Pendiente: conectar el repo en Streamlit Community Cloud
   (share.streamlit.io) para obtener la URL pública y que las 4 ubicaciones reales
   puedan conectarse.
7. ⬜ Integrar ML como motor de demanda/dificultad (NO reemplaza las decisiones humanas)
8. ⬜ Probar con las 4 personas reales, balancear dificultad, demo final

## Notas de entorno
- Trabajar sobre `\\wsl.localhost\ubuntu-22.04\home\dackarl\BEAR GAME` desde Windows,
  o `/home/dackarl/BEAR GAME` desde dentro de WSL.
- Ejecutar comandos de una sola línea vía `wsl.exe -d Ubuntu-22.04 -- bash -lc "..."`.
  Evitar comandos multilínea directos por problemas de CRLF; si se necesita un script
  largo, escribirlo a un `.sh` con la tool Write y ejecutarlo con
  `bash "$HOME/... .sh"` dentro del `-lc`.

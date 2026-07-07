from game.player import Player

ROLES = ["Minorista", "Mayorista", "Distribuidor", "Fabrica"]


def demanda_clasica(ronda):
    """Patron de demanda del Beer Game clasico: 4 unidades las primeras 4 rondas,
    despues salta a 8 y se mantiene. Sirve para probar el motor antes de tener ML."""
    return 4 if ronda <= 4 else 8


class GameState:
    """Orquesta una partida completa: pipelines de pedidos/despachos entre los 4 eslabones.

    Cadena: Cliente -> Minorista -> Mayorista -> Distribuidor -> Fabrica -> (produccion, ilimitada)

    Cada ronda se juega en dos pasos porque en una interfaz real (Streamlit) el jugador
    necesita VER la demanda que le llego antes de decidir cuanto pedir:
      1. start_round()      -> recibe despachos e informa la demanda que le llego a cada rol
      2. complete_round(..) -> aplica las decisiones de pedido, despacha y calcula costos
    """

    def __init__(self, order_delay=2, shipping_delay=2, initial_inventory=12,
                 initial_flow=4, customer_demand_fn=None):
        self.order_delay = order_delay
        self.shipping_delay = shipping_delay
        self.players = {role: Player(role, initial_inventory) for role in ROLES}

        # pedidos en camino hacia cada rol (Minorista no tiene: recibe demanda directa del cliente)
        self.order_pipeline = {role: [initial_flow] * order_delay for role in ROLES[1:]}
        # despachos en camino hacia cada rol (Fabrica incluida: recibe de "produccion")
        self.shipment_pipeline = {role: [initial_flow] * shipping_delay for role in ROLES}

        self.customer_demand_fn = customer_demand_fn or demanda_clasica
        self.round_number = 0
        self.history = []
        self.pending_incoming_demand = None

    def start_round(self):
        """Recibe los despachos que llegan esta ronda y calcula la demanda/pedido
        que le entra a cada jugador. Devuelve un dict role -> cantidad demandada."""
        self.round_number += 1

        for role in ROLES:
            llegada = self.shipment_pipeline[role].pop(0)
            self.players[role].receive_shipment(llegada)

        incoming_demand = {"Minorista": self.customer_demand_fn(self.round_number)}
        for role in ROLES[1:]:
            incoming_demand[role] = self.order_pipeline[role].pop(0)

        self.pending_incoming_demand = incoming_demand
        return incoming_demand

    def complete_round(self, orders):
        """Aplica las decisiones de pedido de cada rol (dict role -> cantidad),
        despacha lo que se puede, actualiza inventario/backlog y calcula costos."""
        if self.pending_incoming_demand is None:
            raise RuntimeError("Hay que llamar start_round() antes de complete_round()")
        incoming_demand = self.pending_incoming_demand

        # el pedido de cada rol entra en transito hacia su proveedor
        for i in range(len(ROLES) - 1):
            role, proveedor = ROLES[i], ROLES[i + 1]
            self.order_pipeline[proveedor].append(orders[role])
        # Fabrica "pide" a produccion -> entra directo a su propio pipeline de despachos
        self.shipment_pipeline["Fabrica"].append(orders["Fabrica"])

        # cada rol despacha lo que puede para cubrir la demanda que recibio
        shipped = {role: self.players[role].fulfill(incoming_demand[role]) for role in ROLES}

        # el despacho de cada rol entra en transito hacia el rol de abajo
        for i in range(1, len(ROLES)):
            role, cliente = ROLES[i], ROLES[i - 1]
            self.shipment_pipeline[cliente].append(shipped[role])
        # el despacho de Minorista va al cliente final (no se modela mas alla)

        costos = {role: self.players[role].compute_cost() for role in ROLES}

        registro = {"ronda": self.round_number}
        for role in ROLES:
            p = self.players[role]
            registro[f"{role}_demanda_recibida"] = incoming_demand[role]
            registro[f"{role}_pedido_realizado"] = orders[role]
            registro[f"{role}_despachado"] = shipped[role]
            registro[f"{role}_inventario"] = p.inventory
            registro[f"{role}_backlog"] = p.backlog
            registro[f"{role}_costo"] = costos[role]
        self.history.append(registro)

        self.pending_incoming_demand = None
        return registro

    def total_cost(self):
        return sum(self.players[role].total_cost for role in ROLES)

class Player:
    """Un eslabon de la cadena (Minorista, Mayorista, Distribuidor o Fabrica)."""

    HOLDING_COST = 0.5   # costo por unidad de inventario que sobra, por ronda
    BACKLOG_COST = 1.0   # costo por unidad de pedido atrasado (backlog), por ronda

    def __init__(self, role, initial_inventory=12):
        self.role = role
        self.inventory = initial_inventory
        self.backlog = 0
        self.total_cost = 0.0

    def receive_shipment(self, quantity):
        """Suma al inventario lo que llego esta ronda desde el proveedor."""
        self.inventory += quantity

    def fulfill(self, demand):
        """Despacha lo que puede para cubrir la demanda recibida + backlog pendiente.
        Devuelve cuanto se despacho realmente. Lo que no alcanza a cubrir queda como backlog."""
        total_needed = demand + self.backlog
        shipped = min(self.inventory, total_needed)
        self.inventory -= shipped
        self.backlog = total_needed - shipped
        return shipped

    def compute_cost(self):
        """Calcula el costo de esta ronda (inventario ocioso + backlog) y lo acumula."""
        cost = self.inventory * self.HOLDING_COST + self.backlog * self.BACKLOG_COST
        self.total_cost += cost
        return cost

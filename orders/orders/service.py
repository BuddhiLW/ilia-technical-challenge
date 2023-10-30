from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko_sqlalchemy import DatabaseSession, Database

from orders.exceptions import NotFound
from orders.models import DeclarativeBase, Order, OrderDetail  # , Orders
from orders.schemas import OrderSchema


class OrdersService:
    name = "orders"

    # db = DatabaseSession(DeclarativeBase)
    db_orders = Database(DeclarativeBase)
    event_dispatcher = EventDispatcher()

    @rpc
    def get_order(self, order_id):
        with self.db_orders.get_session() as session:
            order = session.query(Order).get(order_id)

            if not order:
                raise NotFound("Order with id {} not found".format(order_id))

            return OrderSchema().dump(order).data

    @rpc
    def create_order(self, order_details):
        with self.db_orders.get_session() as session:
            order = Order(
                order_details=[
                    OrderDetail(
                        product_id=order_detail["product_id"],
                        price=order_detail["price"],
                        quantity=order_detail["quantity"],
                    )
                    for order_detail in order_details
                ]
            )

            session.add(order)
            session.commit()

            order = OrderSchema().dump(order).data

            self.event_dispatcher(
                "order_created",
                {
                    "order": order,
                },
            )

            return order

    @rpc
    def update_order(self, order):
        order_details = {
            order_details["id"]: order_details
            for order_details in order["order_details"]
        }
        with self.db_orders.get_session() as session:
            order = session.query(Order).get(order["id"])

            for order_detail in order.order_details:
                order_detail.price = order_details[order_detail.id]["price"]
                order_detail.quantity = order_details[order_detail.id]["quantity"]

            session.commit()

            return OrderSchema().dump(order).data

    @rpc
    def delete_order(self, order_id):
        with self.db_orders.get_session() as session:
            order = session.query(Order).get(order_id)
            session.delete(order)
            session.commit()

    # feature: Get all orders
    @rpc
    def list_orders(self):
        with self.db_orders.get_session() as session:
            orders = list(session.query(Order).all())
            return OrderSchema().dump(orders, many=True).data

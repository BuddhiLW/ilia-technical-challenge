from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko_sqlalchemy import Database, DatabaseSession

from orders.exceptions import NotFound
from orders.models import DeclarativeBase, Order, OrderDetail

# from orders.caching import (
#     cache_create_order,
#     cache_get_order,
#     cache_get_with_redis,
#     cache_list_orders,
#     cache_create_order,
#     cache_get_order,
#     cache_get_with_redis,
#     cache_list_orders,
#     cache_result_with_redis,
# )

from orders.schemas import OrderSchema

from sqlalchemy import create_engine, engine_from_config
from sqlalchemy.orm import scoped_session, sessionmaker

from nameko import config


class OrdersService:
    name = "orders"

    db_orders = DatabaseSession(DeclarativeBase)
    event_dispatcher = EventDispatcher()


    @rpc
    def get_order(self, order_id):
        with self.db_orders as session:
            order = session.query(Order).get(order_id)

            if not order:
                raise NotFound("Order with id {} not found".format(order_id))

            data = OrderSchema().dump(order).data

            session.close()
            return data

    @rpc
    def create_order(self, order_details):
        with self.db_orders as session:
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

            session.close()
            return order

    @rpc
    def update_order(self, order):
        order_details = {
            order_details["id"]: order_details
            for order_details in order["order_details"]
        }

        with self.db_orders as session:
            order = session.query(Order).get(order["id"])

            for order_detail in order.order_details:
                order_detail.price = order_details[order_detail.id]["price"]
                order_detail.quantity = order_details[order_detail.id]["quantity"]

            session.commit()
            data = OrderSchema().dump(order).data
            session.close()

            return data

    @rpc
    def delete_order(self, order_id):
        with self.db_orders as session:
            order = session.query(Order).get(order_id)
            session.delete(order)
            session.commit()
            session.close()

    # feature: Get all orders
    @rpc
    def list_orders(self):
        with self.db_orders as session:
            orders = session.query(Order).all()
            data = OrderSchema().dump(orders, many=True).data

            session.close()
            return data

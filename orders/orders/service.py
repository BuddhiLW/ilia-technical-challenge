from nameko.events import EventDispatcher
from nameko.rpc import rpc
from nameko_sqlalchemy import Database  # DatabaseSession

from orders.exceptions import NotFound
from orders.models import DeclarativeBase, Order, OrderDetail
from orders.caching import (
    # cache_create_order,
    # cache_get_order,
    # cache_get_with_redis,
    # cache_list_orders,
    cache_create_order,
    cache_get_order,
    cache_get_with_redis,
    cache_list_orders,
    cache_result_with_redis,
)
from orders.schemas import OrderSchema

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from nameko import config


class OrdersService:
    name = "orders"

    DB_URIS = "DB_URIS"

    db_orders = Database(DeclarativeBase)
    event_dispatcher = EventDispatcher()
    engine = create_engine(
        config.get(DB_URIS)["orders:Base"], echo=True, pool_recycle=240
    )
    method_session = scoped_session(
        sessionmaker(
            engine,
            expire_on_commit=True,
            autoflush=True,
        )
    )

    @rpc
    @cache_get_order
    @cache_get_with_redis
    @cache_result_with_redis("get_orders", 600)
    def get_order(self, order_id):
        with self.method_session() as session:
            order = session.query(Order).get(order_id)

            if not order:
                raise NotFound("Order with id {} not found".format(order_id))

            data = OrderSchema().dump(order).data

            session.close()
            return data

    @rpc
    @cache_create_order
    @cache_result_with_redis("create_orders", 600)
    def create_order(self, order_details):
        with self.method_session() as session:
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

        with self.method_session() as session:
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
        with self.method_session() as session:
            order = session.query(Order).get(order_id)
            session.delete(order)
            session.commit()
            session.close()
        # order = self.db_orders_session.query(Order).get(order_id)
        # self.db_orders_session.delete(order)
        # self.db_orders_session.commit()

    # feature: Get all orders
    @rpc
    @cache_list_orders
    @cache_result_with_redis("list_orders", 600)
    def list_orders(self):
        with self.method_session() as session:
            orders = session.query(Order).all()
            data = OrderSchema().dump(orders, many=True).data

            session.close()
            return data

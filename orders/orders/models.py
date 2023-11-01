from nameko.rpc import config
from sqlalchemy import Column, Integer, ForeignKey, DECIMAL, DateTime, Index
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

from sqlalchemy import create_engine, engine_from_config
from sqlalchemy.orm import scoped_session, sessionmaker


class Base(object):
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )


DeclarativeBase = declarative_base(cls=Base)
DeclarativeBase.DB_URI = "postgres+psycopg2://postgres:postgres@localhost:5432/orders"


class Order(DeclarativeBase):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)


class OrderDetail(DeclarativeBase):
    __tablename__ = "order_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(
        Integer, ForeignKey("orders.id", name="fk_order_details_orders"), nullable=False
    )
    order = relationship(Order, backref="order_details")
    product_id = Column(Integer, nullable=False)
    price = Column(DECIMAL(18, 2), nullable=False)
    quantity = Column(Integer, nullable=False)


# Add indexes to the columns that are frequently used in queries
Index("order_details_product_id_idx", OrderDetail.product_id)
Index("order_details_order_id_idx", OrderDetail.order_id)

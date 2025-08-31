import logging
from sqlmodel import Session, select
from sqlalchemy import create_engine
import pandas as pd
from functools import partial
from db.models import InventoryItem, Item, Weapon, Armor, Ammo, Consumable
from config import CONFIG
import json
from sqlalchemy.orm import joinedload

# Инициализация движка базы данных
data_engine = create_engine(
    CONFIG.db.db_uri,
    pool_reset_on_return='rollback',
    json_serializer=partial(json.dumps, ensure_ascii=False)
)


def create_object(obj):
    with Session(data_engine) as session:
        session.add(obj)
        session.commit()
        session.refresh(obj)
        logging.info(f"Создан объект в базе данных: {obj}.")
        return obj


def get_object(obj_type, field_name, field_value, options=None):
    with Session(data_engine) as session:
        query = select(obj_type).where(field_name == field_value)
        if options:
            for option in options:
                query = query.options(option)
        obj = session.exec(query).first()
        return obj

def get_objects(obj_type, field_name, field_value, options=None):
    """
    Возвращает все объекты указанного типа, удовлетворяющие условию.
    """
    with Session(data_engine) as session:
        query = select(obj_type).where(field_name == field_value)
        if options:
            for option in options:
                query = query.options(option)
        objects = session.exec(query).all()
        return objects


def update_object(obj, field_name, field_value):
    with Session(data_engine) as session:
        db_obj = get_object(type(obj), field_name, field_value)
        if not db_obj:
            logging.warning(f"Объект {type(obj).__name__} не найден для обновления.")
            raise ValueError(f"Объект {type(obj).__name__} не найден для обновления.")

        # Обновляем поля объекта
        for key, value in vars(obj).items():
            if key.startswith('_') or key == 'metadata':
                continue
            setattr(db_obj, key, value)

        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        logging.info(f"Обновлён объект {db_obj} в базе данных.")
        return db_obj


def delete_object(obj):
    with Session(data_engine) as session:
        session.delete(obj)
        session.commit()
        logging.info(f"Удален объект в базе данных: {obj}")


def fetch_table_as_dataframe(table_name: str, schema: str, connection) -> pd.DataFrame:
    """
    Извлекает таблицу из базы данных в виде DataFrame.

    :param table_name: Название таблицы.
    :param schema: Схема базы данных.
    :param connection: Соединение с базой данных.
    :return: DataFrame с данными таблицы.
    """
    logging.info(f"Извлечение таблицы {schema}.{table_name} из базы данных.")
    df = pd.read_sql_table(table_name, con=connection, schema=schema)
    logging.info(f"Таблица {schema}.{table_name} успешно извлечена.")
    return df


def table_is_empty(table_class):
    with Session(data_engine) as session:
        statement = select(table_class)
        result = session.exec(statement).first()
        return result is None


def get_item_with_subtype(item_id: int):
    """
    Получает предмет с данными из дочерней таблицы.
    """
    with Session(data_engine) as session:
        item = (
            session.query(Item)
            .options(
                joinedload(Item.weapon),
                joinedload(Item.armor),
                joinedload(Item.consumable),
                joinedload(Item.ammo)
            )
            .filter(Item.id == item_id)
            .one_or_none()
        )
        return item


def get_inventory_items_with_subtypes(user_id: int) -> list:
    """
    Возвращает все предметы в инвентаре пользователя с полной загрузкой данных из дочерних таблиц.
    """
    result = []
    with Session(data_engine) as session:
        inventory_items = (
            session.query(InventoryItem)
            .options(
                joinedload(InventoryItem.item.of_type(Weapon)),
                joinedload(InventoryItem.item.of_type(Armor)),
                joinedload(InventoryItem.item.of_type(Consumable)),
                joinedload(InventoryItem.item.of_type(Ammo))
            )
            .filter(InventoryItem.user_id == user_id)
            .all()
        )

        for inv_item in inventory_items:
            item = inv_item.item
            result.append((item, inv_item.quantity))
    return result

import logging
from sqlalchemy import Column, Integer, Unicode, Float, Boolean, ForeignKey, DateTime, BigInteger
from sqlalchemy.orm import relationship, declarative_base, sessionmaker
import json
from functools import partial
from config import CONFIG
import os

from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

Base = declarative_base()

data_engine = create_engine(
    CONFIG.db.db_uri,
    pool_reset_on_return='rollback',
    json_serializer=partial(json.dumps, ensure_ascii=False)
)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, nullable=False, unique=True)
    username = Column(Unicode, nullable=True)
    first_name = Column(Unicode, nullable=True)
    last_name = Column(Unicode, nullable=True)
    added_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, nullable=True)

    character = relationship("Character", back_populates="user", uselist=False)
    inventory = relationship("InventoryItem", back_populates="user")


class Character(Base):
    __tablename__ = 'characters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    nickname = Column(Unicode, nullable=True)
    current_health = Column(Integer, nullable=False, default=100)
    max_health = Column(Integer, nullable=False, default=100)
    level = Column(Integer, nullable=False, default=1)
    experience_points = Column(Integer, nullable=False, default=0)
    money = Column(Integer, nullable=False, default=5000)
    strength = Column(Integer, nullable=False, default=5)
    agility = Column(Integer, nullable=False, default=5)
    intelligence = Column(Integer, nullable=False, default=5)
    charisma = Column(Integer, nullable=False, default=5)
    max_inventory_weight = Column(Integer, nullable=False, default=150)
    current_inventory_weight = Column(Integer, nullable=False, default=0)

    melee_weapon_id = Column(Integer, ForeignKey('items.id'), nullable=True)
    range_weapon_1_id = Column(Integer, ForeignKey('items.id'), nullable=True)
    range_weapon_2_id = Column(Integer, ForeignKey('items.id'), nullable=True)
    armor_id = Column(Integer, ForeignKey('items.id'), nullable=True)

    user = relationship("User", back_populates="character")


class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), nullable=False, unique=True)
    description = Column(Unicode(1024), nullable=True)
    weight = Column(Float, nullable=False, default=0)
    base_price = Column(Integer, nullable=False, default=0)
    stackable = Column(Boolean, nullable=False, default=False)
    type = Column(Unicode(255), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': 'type',
        'polymorphic_identity': 'item'
    }


class Weapon(Item):
    __tablename__ = 'weapons'

    id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    weapon_type = Column(Unicode(50), nullable=False)
    min_level = Column(Integer, nullable=False, default=1)
    min_strength = Column(Integer, nullable=False, default=0)
    min_agility = Column(Integer, nullable=False, default=0)
    min_intelligence = Column(Integer, nullable=False, default=0)
    physical_damage = Column(Integer, nullable=True)
    energy_damage = Column(Integer, nullable=True)
    accuracy = Column(Integer, nullable=True)
    effective_range = Column(Integer, nullable=True)
    ammo_type = Column(Unicode(255), nullable=True)
    magazine_capacity = Column(Integer, nullable=True)
    ap_reload = Column(Integer, nullable=True)
    ap_attack = Column(Integer, nullable=True)
    ap_power_attack = Column(Integer, nullable=True)
    power_attack_ammo = Column(Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'weapon'
    }


class Armor(Item):
    __tablename__ = 'armor'

    id = Column(Integer, ForeignKey('items.id'), primary_key=True)

    min_level = Column(Integer, nullable=False, default=1)
    min_strength = Column(Integer, nullable=False, default=0)
    min_agility = Column(Integer, nullable=False, default=0)
    min_intelligence = Column(Integer, nullable=False, default=0)

    physical_defense = Column(Integer, nullable=False, default=0)
    energy_defense = Column(Integer, nullable=False, default=0)
    chemical_defense = Column(Integer, nullable=False, default=0)

    __mapper_args__ = {
        'polymorphic_identity': 'armor'
    }


class Consumable(Item):
    __tablename__ = 'consumables'

    id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    heal = Column(Integer, nullable=False)
    duration = Column(Integer, nullable=True)
    ap_use = Column(Integer, nullable=True)

    __mapper_args__ = {
        'polymorphic_identity': 'consumable'
    }


class Ammo(Item):
    __tablename__ = 'ammo'

    id = Column(Integer, ForeignKey('items.id'), primary_key=True)
    ammo_type = Column(Unicode(255), nullable=False)
    damage_modifier = Column(Float, nullable=True, default=1.0)

    __mapper_args__ = {
        'polymorphic_identity': 'ammo'
    }


class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)

    user = relationship("User", back_populates="inventory")
    item = relationship("Item")


class Enemy(Base):
    __tablename__ = 'enemies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(255), nullable=False, unique=True)
    accuracy = Column(Integer, nullable=True)
    effective_range = Column(Integer, nullable=True)
    base_health = Column(Integer, nullable=False, default=0)
    health_per_level = Column(Integer, nullable=False, default=0)
    base_physical_defense = Column(Integer, nullable=False, default=0)
    physical_defense_per_level = Column(Integer, nullable=False, default=0)
    base_energy_defense = Column(Integer, nullable=False, default=0)
    energy_defense_per_level = Column(Integer, nullable=False, default=1)
    base_chemical_defense = Column(Integer, nullable=False, default=0)
    chemical_defense_per_level = Column(Integer, nullable=False, default=0)
    base_physical_damage = Column(Integer, nullable=False, default=0)
    physical_damage_per_level = Column(Integer, nullable=False, default=0)
    base_energy_damage = Column(Integer, nullable=False, default=0)
    energy_damage_per_level = Column(Integer, nullable=False, default=0)
    base_chemical_damage = Column(Integer, nullable=False, default=0)
    chemical_damage_per_level = Column(Integer, nullable=False, default=0)


class BattleState(Base):
    __tablename__ = 'battle_states'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    enemies_data = Column(Unicode(1024), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)


Base.metadata.create_all(data_engine)

# Функция для инициализации данных
def initialize_items_table(engine, json_file):
    Session = sessionmaker(bind=data_engine)
    session = Session()

    try:
        logging.info("Начинаем инициализацию данных из JSON.")
        with open(json_file, "r", encoding="utf-8") as f:
            items = json.load(f)

        for item_data in items:
            existing_item = session.query(Item).filter_by(name=item_data["name"]).first()
            if existing_item:
                logging.info(f"Предмет '{item_data['name']}' уже существует в базе данных.")
                continue

            if item_data["type"] == "weapon":
                item = Weapon(
                    name=item_data["name"],
                    description=item_data.get("description"),
                    weight=item_data["weight"],
                    base_price=item_data["base_price"],
                    stackable=item_data["stackable"],
                    weapon_type=item_data["weapon_type"],
                    min_level=item_data.get("min_level", 1),
                    min_strength=item_data.get("min_strength", 0),
                    min_agility=item_data.get("min_agility", 0),
                    min_intelligence=item_data.get("min_intelligence", 0),
                    physical_damage=item_data.get("physical_damage"),
                    energy_damage=item_data.get("energy_damage"),
                    accuracy=item_data.get("accuracy"),
                    effective_range=item_data.get("effective_range"),
                    ammo_type=item_data.get("ammo_type"),
                    magazine_capacity=item_data.get("magazine_capacity"),
                    ap_reload=item_data.get("ap_reload"),
                    ap_attack=item_data.get("ap_attack"),
                    ap_power_attack=item_data.get("ap_power_attack"),
                    power_attack_ammo=item_data.get("power_attack_ammo")
                )
            elif item_data["type"] == "armor":
                item = Armor(
                    name=item_data["name"],
                    description=item_data.get("description"),
                    weight=item_data["weight"],
                    base_price=item_data["base_price"],
                    stackable=item_data["stackable"],
                    min_level=item_data.get("min_level", 1),
                    min_strength=item_data.get("min_strength", 0),
                    min_agility=item_data.get("min_agility", 0),
                    min_intelligence=item_data.get("min_intelligence", 0),
                    physical_defense=item_data.get("physical_defense"),
                    energy_defense=item_data.get("energy_defense"),
                    chemical_defense=item_data.get("chemical_defense")
                )
            elif item_data["type"] == "consumable":
                item = Consumable(
                    name=item_data["name"],
                    description=item_data.get("description"),
                    weight=item_data["weight"],
                    base_price=item_data["base_price"],
                    stackable=item_data["stackable"],
                    heal=item_data.get("heal"),
                    duration=item_data.get("duration"),
                    ap_use=item_data.get("ap_use")
                )
            elif item_data["type"] == "ammo":
                item = Ammo(
                    name=item_data["name"],
                    description=item_data.get("description"),
                    weight=item_data["weight"],
                    base_price=item_data["base_price"],
                    stackable=item_data["stackable"],
                    ammo_type=item_data.get("ammo_type"),
                    damage_modifier=item_data.get("damage_modifier")
                )
            session.add(item)
            logging.info(f"Добавлен предмет '{item_data['name']}' в базу данных.")

        session.commit()
        logging.info("Инициализация данных завершена.")
    except Exception as e:
        logging.error(f"Ошибка при инициализации данных: {e}")
        session.rollback()
    finally:
        session.close()

json_file_path = os.path.join("game", "data", "items.json")
initialize_items_table(data_engine, json_file_path)
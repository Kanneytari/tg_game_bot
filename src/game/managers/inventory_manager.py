from typing import List, Dict
from sqlalchemy.orm import Session
from db.models import InventoryItem, Item, Character, Weapon, Armor, Consumable, Ammo
from db.helper import get_objects, get_object, create_object, update_object, delete_object
from sqlalchemy.orm import joinedload
from db.models import data_engine
from game.managers.character_manager import CharacterManager
from db.helper import get_inventory_items_with_subtypes

class InventoryManager:

    @staticmethod
    def generate_inventory_message(user_id: int) -> str:
        """
        Генерирует сообщение об инвентаре пользователя с полной загрузкой данных о дочерних объектах.
        """
        character = get_object(Character, Character.user_id, user_id)
        inventory_items = get_inventory_items_with_subtypes(user_id)

        if not inventory_items:
            return f"🎒 Ваш инвентарь пуст.\n\n💵: {character.money}"

        items_data_dict = {
            "armor": [],
            "weapon": {"melee": [], "firearm": [], "energy": []},
            "consumable": [],
            "ammo": []
        }

        weapon_type_translation = {
            "melee": "Холодное оружие",
            "firearm": "Огнестрельное оружие",
            "energy": "Энергетическое оружие",
        }

        for item, quantity in inventory_items:
            if item.type == "weapon":
                weapon_type = getattr(item, "weapon_type", None)
                if weapon_type and weapon_type.lower() in items_data_dict["weapon"]:
                    items_data_dict["weapon"][weapon_type.lower()].append((item, quantity))
            elif item.type == "armor":
                items_data_dict["armor"].append((item, quantity))
            elif item.type == "consumable":
                items_data_dict["consumable"].append((item, quantity))
            elif item.type == "ammo":
                items_data_dict["ammo"].append((item, quantity))

        def format_items(title, items):
            if not items:
                return ""
            section = f"**{title}:**\n"
            for item, quantity in items:
                command = f"/item_stat_{item.id}"
                if item.stackable:
                    section += f"--- {item.name} [x {quantity}] {command}\n"
                else:
                    section += f"--- {item.name} ({command})\n" * quantity
            section += "\n"
            return section

        def format_nested_items(title, nested_items):
            if not any(nested_items.values()):
                return ""
            section = f"**{title}:**\n"
            for subtype, items in nested_items.items():
                if items:
                    translated_subtype = weapon_type_translation.get(subtype, subtype.capitalize())
                    section += f"- {translated_subtype}:\n"
                    for item, quantity in items:
                        command = f"/item_stat_{item.id}"
                        if item.stackable:
                            section += f"--- {item.name} [x {quantity}] {command}\n"
                        else:
                            section += f"--- {item.name} ({command})\n" * quantity
            section += "\n"
            return section

        message = f"🎒 **Инвентарь [{character.current_inventory_weight} / {character.max_inventory_weight}]:**\n\n"
        message += format_items("Броня", items_data_dict["armor"])
        message += format_nested_items("Оружие", items_data_dict["weapon"])
        message += format_items("Боеприпасы", items_data_dict["ammo"])
        message += format_items("Медикаменты", items_data_dict["consumable"])
        message += f"💵: {character.money}"

        return message

        def format_nested_items(title, nested_items):
            if not any(nested_items.values()):
                return ""
            section = f"**{title}:**\n"
            for subtype, items in nested_items.items():
                if items:
                    translated_subtype = weapon_type_translation.get(subtype, subtype.capitalize())
                    section += f"__{translated_subtype}__:\n"
                    for item, quantity in items:
                        if item.stackable:
                            section += f"--- {item.name} [x {quantity}]\n"
                        else:
                            section += f"--- {item.name}\n" * quantity
            section += "\n"
            return section

        message = f"🎒 **Инвентарь [{character.current_inventory_weight} / {character.max_inventory_weight}]:**\n\n"
        message += format_items("Броня", items_data_dict["armor"])
        message += format_nested_items("Оружие", items_data_dict["weapon"])
        message += format_items("Боеприпасы", items_data_dict["ammo"])
        message += format_items("Медикаменты", items_data_dict["consumable"])
        message += f"💵: {character.money}"

        return message

    @staticmethod
    def add_item(user_id: int, item_id: int, quantity: int = 1) -> bool:
        """
        Добавляет предмет в инвентарь персонажа, проверяя вместимость.
        """
        character = get_object(Character, Character.user_id, user_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        item = get_object(Item, Item.id, item_id)
        if not item:
            raise ValueError("Предмет не найден!")

        current_weight = InventoryManager.calculate_current_weight(user_id=character.user_id)
        max_weight = character.max_inventory_weight

        if current_weight + item.weight * quantity > max_weight:
            return False

        inventory_items = get_objects(InventoryItem, InventoryItem.user_id, user_id)
        if inventory_items:
            for inv_item in inventory_items:
                if inv_item.item_id == item.id:
                    inv_item.quantity += quantity
                    update_object(inv_item, InventoryItem.id, inv_item.id)
                    InventoryManager.update_inventory_weight(user_id)
                    return True

        create_object(InventoryItem(user_id=user_id, item_id=item_id, quantity=quantity))
        InventoryManager.update_inventory_weight(user_id)
        return True



    @staticmethod
    def remove_item(user_id: int, inventory_item_id: int, quantity: int = 1) -> bool:
        """
        Удаляет предмет из инвентаря или уменьшает его количество.
        """
        inventory_item = get_object(InventoryItem, InventoryItem.id, inventory_item_id)
        if not inventory_item or inventory_item.user_id != user_id:
            return False
        if inventory_item.quantity < quantity:
            return False
        elif inventory_item.quantity >= quantity:
            inventory_item.quantity -= quantity
            update_object(inventory_item, InventoryItem.id, inventory_item.id)
            if inventory_item.quantity == 0:
                CharacterManager.unequip_item(user_id=user_id,
                                              item_id=inventory_item.item_id)
        InventoryManager.update_inventory_weight(user_id)
        return True

    @staticmethod
    def calculate_current_weight(user_id) -> float:
        """
        Рассчитывает текущий вес всех предметов в инвентаре.
        """
        weight = 0
        inventory_items = get_objects(InventoryItem, InventoryItem.user_id, int(user_id))
        for inv_item in inventory_items:
            item_data = get_object(Item, Item.id, inv_item.item_id)
            weight += item_data.weight * inv_item.quantity
        return round(weight, 2)

    @staticmethod
    def calculate_max_weight(character_level: int, character_strength: int) -> int:
        """
        Рассчитывает максимальную грузоподъемность на основе уровня и силы персонажа.
        """
        return character_strength * 10 + 100

    @staticmethod
    def format_inventory_message(inventory_items: List[Dict]) -> str:
        """
        Форматирует список предметов в инвентаре для отображения в виде сообщения.
        """
        if not inventory_items:
            return "\ud83d\udce6 Ваш инвентарь пуст."

        lines = [
            f"{item['name']} x{item['quantity']} (Вес: {item['weight']} кг)"
            for item in inventory_items
        ]
        total_weight = sum(item["weight"] for item in inventory_items)
        return "\n".join(lines) + f"\n\u2696\ufe0f Общий вес: {total_weight} кг"

    @staticmethod
    def update_inventory_weight(user_id: int) -> None:
        """
        Пересчитывает текущий вес инвентаря пользователя.
        """
        character = get_object(Character, Character.user_id, user_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        current_weight = InventoryManager.calculate_current_weight(user_id=user_id)
        character.current_inventory_weight = current_weight
        update_object(character, Character.id, character.id)

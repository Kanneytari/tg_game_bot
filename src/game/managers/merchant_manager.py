import logging
from db.models import Item, Character, InventoryItem
from db.helper import get_object, update_object, get_objects
from game.managers.inventory_manager import InventoryManager


class MerchantManager:

    @staticmethod
    def purchase_item(user_id: int, item_id: int, quantity: int = 1) -> str:
        """
        Обработка покупки товара: проверка вместимости инвентаря и баланса персонажа.
        """
        character = get_object(Character, Character.user_id, user_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        item = get_object(Item, Item.id, item_id)
        if not item:
            return "Товар не найден!"

        total_price = item.base_price * quantity
        if character.money < total_price:
            return "Недостаточно денег для покупки!"
        current_weight = InventoryManager.calculate_current_weight(user_id=character.user_id)

        if current_weight + item.weight * quantity > character.max_inventory_weight:
            return "Недостаточно места в инвентаре!"

        if InventoryManager.add_item(character.user_id, item_id, quantity):
            character.money -= total_price
            update_object(character, Character.id, character.id)
            InventoryManager.update_inventory_weight(character.user_id)
            return f"Вы успешно купили {quantity} x {item.name} за {total_price} монет."
        else:
            return "Ошибка при добавлении товара в инвентарь."

    @staticmethod
    def sell_item(user_id: int, inventory_item_id: int, quantity: int = 1) -> str:
        """
        Обработка продажи предмета из инвентаря персонажа.
        """
        character = get_object(Character, Character.user_id, user_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        inventory_item = get_object(InventoryItem, InventoryItem.id, inventory_item_id)
        if not inventory_item or inventory_item.user_id != character.user_id:
            return "Предмет не найден в инвентаре!"

        if inventory_item.quantity < quantity:
            return "Недостаточно предметов для продажи!"

        item = get_object(Item, Item.id, inventory_item.item_id)
        total_price = item.base_price * quantity

        if InventoryManager.remove_item(character.user_id, inventory_item_id, quantity):
            InventoryManager.update_inventory_weight(user_id=character.user_id)
            character = get_object(Character, Character.user_id, user_id)
            character.money += total_price
            update_object(character, Character.id, character.id)
            return f"Вы успешно продали {quantity} x {item.name} за {total_price} монет."
        else:
            return "Ошибка при удалении предмета из инвентаря."

    @staticmethod
    def get_categories() -> list:
        return ["Оружие", "Броня", "Патроны", "Медикаменты"]

    @staticmethod
    def translate_category_to_db(category: str) -> str:
        category_map = {
            "Оружие": "weapon",
            "Броня": "armor",
            "Патроны": "ammo",
            "Медикаменты": "consumable",
        }
        return category_map.get(category, "")

    @staticmethod
    def get_items_by_type(type: str) -> list:
        return [
            {
                "id": item.id,
                "name": item.name,
                "base_price": item.base_price
            }
            for item in get_objects(Item, Item.type, type)
        ]

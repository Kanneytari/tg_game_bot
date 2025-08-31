from telethon.tl.custom import Button
from db.helper import get_object, get_objects, update_object
from db.models import Character, Item, InventoryItem, User, Weapon, Armor
from game.managers.character_manager import CharacterManager

async def handle_equip_command(event):
    buttons = [
        [Button.inline("Броня", b"equip_slot_armor")],
        [Button.inline("Холодное оружие", b"equip_slot_melee_weapon")],
        [Button.inline("Дальнобойное оружие 1", b"equip_slot_range_weapon_1")],
        [Button.inline("Дальнобойное оружие 2", b"equip_slot_range_weapon_2")],
    ]
    await event.respond("Выберите слот для экипировки:", buttons=buttons)

async def handle_equip_slot(event, slot):
    user = get_object(User, User.telegram_id, event.sender_id)
    character = get_object(Character, Character.user_id, user.id)
    inventory_items = get_objects(InventoryItem, InventoryItem.user_id, user.id)

    available_items = []
    if slot == "melee_weapon":
        # Фильтруем только холодное оружие
        for inv_item in inventory_items:
            item_data = get_object(Item, Item.id, inv_item.item_id)
            if item_data.type == "weapon":
                weapon_data = get_object(Weapon, Weapon.id, item_data.id)
                if weapon_data.weapon_type.lower() == "melee":
                    available_items.append({"id": item_data.id, "name": item_data.name})
    elif slot in ["range_weapon_1", "range_weapon_2"]:
        # Фильтруем только дальнобойное оружие
        for inv_item in inventory_items:
            item_data = get_object(Item, Item.id, inv_item.item_id)
            if item_data.type == "weapon":
                weapon_data = get_object(Weapon, Weapon.id, item_data.id)
                if weapon_data.weapon_type.lower() != "melee":
                    if slot == "range_weapon_1":
                        if character.range_weapon_2_id != weapon_data.id:
                            available_items.append({"id": item_data.id, "name": item_data.name})
                    if slot == "range_weapon_2":
                        if character.range_weapon_1_id != weapon_data.id:
                            available_items.append({"id": item_data.id, "name": item_data.name})
    elif slot == "armor":
        # Фильтруем только броню
        for inv_item in inventory_items:
            item_data = get_object(Item, Item.id, inv_item.item_id)
            if item_data.type == "armor":
                available_items.append({"id": item_data.id, "name": item_data.name})

    if not available_items:
        await event.respond("❌ У вас нет подходящих предметов для этого слота.")
        return

    # Генерация кнопок для доступных предметов
    buttons = [
        [Button.inline(f"{item['name']} ✅" if getattr(character, f"{slot}_id") == item['id'] else item['name'],
                       f"equip_item_{item['id']}_{slot}")]
        for item in available_items
    ]
    await event.respond("Выберите предмет для экипировки:", buttons=buttons)

async def handle_equip_item(event, item_id, slot):
    user = get_object(User, User.telegram_id, event.sender_id)
    character = get_object(Character, Character.user_id, user.id)
    item = get_object(Item, Item.id, item_id)

    if not CharacterManager.check_item_requirements(character, item):
        await event.respond("❌ Ваш персонаж не соответствует минимальным требованиям предмета.")
        return

    setattr(character, f"{slot}_id", item_id)
    update_object(character, Character.user_id, user.id)
    await event.respond("✅ Предмет успешно экипирован!")

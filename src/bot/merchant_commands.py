from telethon.tl.custom import Button
from telethon import events
from db.helper import get_object, get_objects
from db.models import Character, Item, InventoryItem, User
from game.managers.merchant_manager import MerchantManager
import logging


async def handle_merchant_main_menu(event, is_new_message=False):
    """
    Главное меню торговца.
    """
    buttons = [
        [Button.inline("🛒 Покупка предметов", b"merchant:buy")],
        [Button.inline("💰 Продажа предметов", b"merchant:sell")],
    ]
    if is_new_message:
        await event.respond("📜 Выберите действие:", buttons=buttons)
    else:
        await event.edit("📜 Выберите действие:", buttons=buttons)


async def handle_merchant_command(event, command_data):
    """
    Обработка команд торговца.
    """
    command_parts = command_data.split(":")

    if command_parts[1] == "main_menu":
        await handle_merchant_main_menu(event)

    elif command_parts[1] == "buy":
        await handle_buy_menu(event)

    elif command_parts[1] == "sell":
        await handle_sell_menu(event)

    elif command_parts[1] == "sell_menu":
        await handle_sell_menu(event)  # Обработка команды возврата в меню продажи

    elif command_parts[1] == "select_category":
        category = command_parts[2]
        await handle_category_selection(event, category)

    elif command_parts[1] == "item_details":
        item_id = int(command_parts[2])
        await handle_item_details(event, item_id)

    elif command_parts[1] == "purchase_item":
        user = get_object(User, User.telegram_id, event.sender_id)
        character = get_object(Character, Character.user_id, user.id)
        item_id = int(command_parts[2])
        await handle_purchase_item(event, character, item_id)

    elif command_parts[1] == "sell_item":
        inventory_item_id = int(command_parts[2])
        user = get_object(User, User.telegram_id, event.sender_id)
        character = get_object(Character, Character.user_id, user.id)
        await handle_sell_item(event, character, inventory_item_id)

    elif command_parts[1] == "go_back":
        await handle_merchant_main_menu(event)

    else:
        await event.edit("❌ Неизвестная команда.")


async def handle_buy_menu(event):
    """
    Меню покупки предметов.
    """
    buttons = [
        [Button.inline("Оружие", b"merchant:select_category:weapon")],
        [Button.inline("Броня", b"merchant:select_category:armor")],
        [Button.inline("Патроны", b"merchant:select_category:ammo")],
        [Button.inline("Медикаменты", b"merchant:select_category:consumable")],
        [Button.inline("Назад", b"merchant:main_menu")]
    ]
    await event.edit("Выберите категорию:", buttons=buttons)


async def handle_category_selection(event, category):
    """
    Выбор предметов из категории.
    """
    items = MerchantManager.get_items_by_type(category)
    if not items:
        await event.edit("❌ Предметы не найдены.", buttons=[[Button.inline("Назад", b"merchant:buy")]])
        return

    buttons = [
                  [Button.inline(f"{item['name']} ({item['base_price']}💵)", f"merchant:item_details:{item['id']}")]
                  for item in items
              ] + [[Button.inline("Назад", b"merchant:buy")]]
    await event.edit("Выберите предмет:", buttons=buttons)


async def handle_item_details(event, item_id):
    """
    Подробности о предмете.
    """
    from game.managers.item_manager import ItemManager

    message = ItemManager.generate_item_stat_message(item_id)
    if not message:
        await event.edit("❌ Предмет не найден.", buttons=[[Button.inline("Назад", b"merchant:buy")]])
        return

    buttons = [
        [Button.inline("Купить", f"merchant:purchase_item:{item_id}")],
        [Button.inline("Назад", b"merchant:buy")]
    ]
    await event.edit(message, buttons=buttons)


async def handle_purchase_item(event, character, item_id):
    """
    Покупка предмета. Ожидание ввода количества при необходимости.
    """
    item = get_object(Item, Item.id, item_id)

    if item.stackable:
        await event.edit(
            "Введите количество для покупки или нажмите 'Отмена':",
            buttons=[[Button.inline("Отмена", b"merchant:buy")]]
        )

        @event.client.on(events.NewMessage(from_users=event.sender_id))
        async def handle_quantity_input(new_event):
            try:
                quantity = int(new_event.text)
                if quantity <= 0:
                    await new_event.respond("❌ Количество должно быть больше нуля.")
                    return

                response = MerchantManager.purchase_item(character.user_id, item_id, quantity)

                # Изменение сообщения после успешной покупки
                await event.edit(
                    f"✅ {response}",
                    buttons=[[Button.inline("Назад", b"merchant:buy")]]
                )
            except ValueError:
                await new_event.respond("❌ Введите корректное число.")
            finally:
                event.client.remove_event_handler(handle_quantity_input)
    else:
        response = MerchantManager.purchase_item(character.user_id, item_id, 1)
        await event.edit(
            f"✅ {response}",
            buttons=[[Button.inline("Назад", b"merchant:buy")]]
        )



async def handle_sell_menu(event):
    """
    Меню продажи предметов.
    """
    user = get_object(User, User.telegram_id, event.sender_id)
    inventory_items = get_objects(InventoryItem, InventoryItem.user_id, user.id)

    # Фильтрация предметов с quantity < 1
    inventory_items = [inv_item for inv_item in inventory_items if inv_item.quantity > 0]

    if not inventory_items:
        await event.edit("❌ У вас нет предметов для продажи.",
                         buttons=[[Button.inline("Назад", b"merchant:main_menu")]])
        return

    buttons = []
    for inv_item in inventory_items:
        item = get_object(Item, Item.id, inv_item.item_id)

        # Формируем текст кнопки
        if item.stackable or inv_item.quantity > 1:
            button_text = f"{item.name} ({inv_item.quantity})"
        else:
            button_text = item.name

        buttons.append([Button.inline(button_text, f"merchant:sell_item:{inv_item.id}")])

    buttons.append([Button.inline("Назад", b"merchant:main_menu")])
    await event.edit("Выберите предмет для продажи:", buttons=buttons)


async def handle_sell_item(event, character, inventory_item_id):
    """
    Продажа предмета. Ожидание ввода количества при необходимости.
    """
    inventory_item = get_object(InventoryItem, InventoryItem.id, inventory_item_id)
    item = get_object(Item, Item.id, inventory_item.item_id)

    if item.stackable:
        await event.edit(
            "Введите количество для продажи или нажмите 'Отмена':",
            buttons=[[Button.inline("Отмена", b"merchant:sell_menu")]]
        )

        @event.client.on(events.NewMessage(from_users=event.sender_id))
        async def handle_quantity_input(new_event):
            try:
                quantity = int(new_event.text)
                if quantity <= 0:
                    await new_event.respond("❌ Некорректное количество.")
                    return
                if quantity > inventory_item.quantity:
                    await new_event.respond(f"❌ Вы можете продать только {inventory_item.quantity} шт.")
                    return

                response = MerchantManager.sell_item(character.user_id, inventory_item_id, quantity)

                # Изменение сообщения после успешной продажи
                await event.edit(
                    f"✅ {response}",
                    buttons=[[Button.inline("Назад", b"merchant:sell_menu")]]
                )
            except ValueError:
                await new_event.respond("❌ Введите корректное число.")
            finally:
                event.client.remove_event_handler(handle_quantity_input)
    else:
        response = MerchantManager.sell_item(character.user_id, inventory_item_id, 1)
        await event.edit(
            f"✅ {response}",
            buttons=[[Button.inline("Назад", b"merchant:sell_menu")]]
        )


import logging
from telethon import events
from db.helper import get_object
from db.models import User, Character
from bot.merchant_commands import (
    handle_merchant_main_menu,
    handle_merchant_command,
)
from bot.equip_commands import (
    handle_equip_command,
    handle_equip_slot,
    handle_equip_item,
)
from game.managers.item_manager import ItemManager

async def update_last_activity(user):
    """
    Обновляет время последней активности пользователя.
    """
    from datetime import datetime
    user.last_activity = datetime.utcnow()
    from db.helper import update_object
    update_object(user, User.id, user.id)

async def start_command(event: events.NewMessage.Event):
    """
    Обрабатывает команду /start, создавая нового пользователя и персонажа при необходимости.
    """
    from game.managers.character_manager import CharacterManager

    telegram_id = event.sender_id
    username = event.sender.username
    first_name = event.sender.first_name

    logging.info(f"Processing /start command for user {telegram_id} ({username}).")

    user, character, is_new_user = CharacterManager.ensure_user_and_character(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name
    )

    if is_new_user:
        await event.respond(f"\ud83d\udc4b Добро пожаловать, {character.nickname}! Ваш персонаж создан.")
    else:
        await update_last_activity(user)
        await event.respond(f"\ud83d\udc4b Добро пожаловать обратно, {character.nickname}!")


    # Отправка информации о персонаже
    profile_message = CharacterManager.generate_profile_message(character)
    await event.respond(profile_message)

async def profile_command(event: events.NewMessage.Event):
    """
    Обрабатывает команду /profile, отображая информацию о персонаже пользователя.
    """
    from game.managers.character_manager import CharacterManager

    telegram_id = event.sender_id
    logging.info(f"Processing /profile command for user {telegram_id}.")
    user = get_object(User, User.telegram_id, telegram_id)
    if not user:
        await event.respond("❌ Пользователь не найден.")
        return
    character = get_object(Character, Character.user_id, user.id)
    if not character:
        await event.respond("❌ Персонаж не найден.")
        return
    await update_last_activity(user)
    profile_message = CharacterManager.generate_profile_message(character)
    await event.respond(profile_message)


async def merchant_command(event: events.NewMessage.Event):
    """
    Обрабатывает команду /merchant, показывая меню торговца.
    """
    logging.info(f"Processing /merchant command for user {event.sender_id}.")
    user = get_object(User, User.telegram_id, event.sender_id)
    await update_last_activity(user)
    await handle_merchant_main_menu(event, is_new_message=True)

async def equip_command(event: events.NewMessage.Event):
    """
    Обрабатывает команду /equip, позволяя игроку выбрать слот для экипировки.
    """
    logging.info(f"Processing /equip command for user {event.sender_id}.")
    await handle_equip_command(event)

async def callback_handler(event: events.CallbackQuery.Event):
    """
    Универсальный обработчик для всех инлайн-кнопок.
    Делегирует обработку команд с префиксом 'merchant_' или 'equip_' в соответствующие модули.
    """
    callback_data = event.data.decode("utf-8")
    logging.info(f"Callback received: {callback_data}")

    user = get_object(User, User.telegram_id, event.sender_id)
    if not user:
        await event.answer("❌ Сначала используйте команду /start для создания персонажа.", alert=True)
        return

    await update_last_activity(user)

    if callback_data.startswith("merchant:"):
        from bot.merchant_commands import handle_merchant_command
        await handle_merchant_command(event, callback_data)
    elif callback_data.startswith("equip_"):
        from bot.equip_commands import handle_equip_slot, handle_equip_item
        if callback_data.startswith("equip_slot_"):
            slot = callback_data[len("equip_slot_"):]  # Извлекаем слот
            await handle_equip_slot(event, slot)
        elif callback_data.startswith("equip_item_"):
            data = callback_data[len("equip_item_"):]  # Извлекаем item_id и slot
            item_id, slot = data.split("_", 1)
            await handle_equip_item(event, int(item_id), slot)
    else:
        await event.answer("❌ Неизвестная команда.", alert=True)


async def inventory_command(event: events.NewMessage.Event):
    """
    Обрабатывает команду /inventory, отображая содержимое инвентаря пользователя.
    """
    from game.managers.inventory_manager import InventoryManager
    telegram_id = event.sender_id
    logging.info(f"Processing /inventory command for user {telegram_id}.")

    user = get_object(User, User.telegram_id, telegram_id)
    if not user:
        await event.respond("❌ Пользователь не найден. Сначала используйте команду /start для создания персонажа.")
        return

    inventory_message = InventoryManager.generate_inventory_message(user.id)
    await event.respond(inventory_message)

async def item_stat_command(event):
    command = event.text.strip()
    try:
        item_id = int(command.split("_")[-1])
    except ValueError:
        await event.respond("❌ Неверный формат команды. Используйте /item_stat_{item_id}.")
        return

    from game.managers.item_manager import ItemManager
    message = ItemManager.generate_item_stat_message(item_id)
    await event.respond(message)


def add_event_handlers(client):
    """
    Регистрирует все обработчики событий для бота.
    """
    client.add_event_handler(start_command, events.NewMessage(pattern='/start'))
    client.add_event_handler(profile_command, events.NewMessage(pattern='/profile'))
    client.add_event_handler(merchant_command, events.NewMessage(pattern='/merchant'))
    client.add_event_handler(equip_command, events.NewMessage(pattern='/equip'))
    client.add_event_handler(inventory_command, events.NewMessage(pattern='/inventory'))
    client.add_event_handler(item_stat_command, events.NewMessage(pattern="/item_stat_\\d+"))
    client.add_event_handler(callback_handler, events.CallbackQuery)

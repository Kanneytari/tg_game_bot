import logging
from db.models import Character, Item, User, Armor, Weapon
from db.helper import get_object, update_object, create_object
import datetime

class CharacterManager:

    @staticmethod
    def ensure_user_and_character(telegram_id: int, username: str, first_name: str):
        """
        Проверяет существование пользователя и персонажа. Создает их при необходимости.
        """
        user = get_object(User, User.telegram_id, telegram_id)
        is_new_user = False

        if not user:
            user = create_object(User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                added_at=datetime.datetime.utcnow(),
                last_activity=datetime.datetime.utcnow()
            ))
            is_new_user = True

        character = get_object(Character, Character.user_id, user.id)
        if not character:
            # Формируем nickname
            nickname = username.capitalize() if username else f"id{telegram_id}"
            character = CharacterManager.create_character(user.id, nickname)
            is_new_user = True

        return user, character, is_new_user

    @staticmethod
    def generate_profile_message(character: Character) -> str:
        """
        Формирует текстовое сообщение с профилем персонажа.
        """
        from db.helper import get_object
        from game.managers.inventory_manager import InventoryManager
        # Инвентарь
        current_weight = InventoryManager.calculate_current_weight(character.user_id)
        max_weight = character.max_inventory_weight

        # Форматируем характеристики персонажа
        profile = (
                f"**Профиль {character.nickname}**\n\n"
                f"⭐️ Уровень: {character.level}\n"
                f"🎓 Опыт: {character.experience_points}\n"
                f"❤️‍🩹 Здоровье: {character.current_health}/{character.max_health}\n"
                f"💵 Деньги: {character.money:,}".replace(",", " ") + "\n"
                f"🎒 Инвентарь: [{current_weight:.1f} / {max_weight}]\n\n"
        )


        # Характеристики
        profile += (
            f"📊 **Характеристики:**\n"
            f"💪 {character.strength}, 🏃 {character.agility}, 🔬 {character.intelligence}, 🧲 {character.charisma}\n\n"
        )

        # Экипировка
        profile += "👕️ **Экипировка:**\n"

        # Броня
        armor = get_object(Armor, Armor.id, character.armor_id)
        if armor:
            armor_stats = []
            if armor.physical_defense > 0:
                armor_stats.append(f"🛡 {armor.physical_defense}")
            if armor.energy_defense > 0:
                armor_stats.append(f"⚡️ {armor.energy_defense}")
            if armor.chemical_defense > 0:
                armor_stats.append(f"🧪 {armor.chemical_defense}")
            armor_stats_str = ", ".join(armor_stats)
            profile += f"**- Броня:**\n--- {armor.name} [{armor_stats_str}]\n"

        # Оружие
        weapons = []

        # Холодное оружие
        melee_weapon = get_object(Weapon, Weapon.id, character.melee_weapon_id)
        if melee_weapon:
            weapons.append(f"--- {melee_weapon.name} [💥 {melee_weapon.physical_damage}]")

        # Дальнобойное оружие 1
        range_weapon_1 = get_object(Weapon, Weapon.id, character.range_weapon_1_id)
        if range_weapon_1:
            range_stats = []
            if range_weapon_1.physical_damage > 0:
                range_stats.append(f"💥 {range_weapon_1.physical_damage}")
            if range_weapon_1.accuracy > 0:
                range_stats.append(f"🎯 {range_weapon_1.accuracy}")
            if range_weapon_1.effective_range > 0:
                range_stats.append(f"📏 {range_weapon_1.effective_range}")
            weapons.append(f"--- {range_weapon_1.name} [{', '.join(range_stats)}]")

        # Дальнобойное оружие 2
        range_weapon_2 = get_object(Weapon, Weapon.id, character.range_weapon_2_id)
        if range_weapon_2:
            range_stats = []
            if range_weapon_2.physical_damage > 0:
                range_stats.append(f"💥 {range_weapon_2.physical_damage}")
            if range_weapon_2.accuracy > 0:
                range_stats.append(f"🎯 {range_weapon_2.accuracy}")
            if range_weapon_2.effective_range > 0:
                range_stats.append(f"📏 {range_weapon_2.effective_range}")
            weapons.append(f"--- {range_weapon_2.name} [{', '.join(range_stats)}]")

        if weapons:
            profile += "**- Оружие:**\n" + "\n".join(weapons) + "\n"

        return profile

    @staticmethod
    def create_character(user_id: int, nickname: str) -> Character:
        """
        Создает нового персонажа для пользователя.
        """
        character = Character(
            user_id=user_id,
            nickname=nickname,
            current_health=100,
            max_health=100,
            level=1,
            experience_points=0,
            money=5000,
            strength=5,
            agility=5,
            intelligence=5,
            charisma=5,
            max_inventory_weight=150
        )
        return create_object(character)

    @staticmethod
    def revive_character(character_id: int) -> Character:
        """
        Воскрешает персонажа с полным здоровьем.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        character.current_health = character.max_health
        return update_object(character, Character.id, character_id)

    @staticmethod
    def change_health(character_id: int, health_points: int) -> Character:
        """
        Меняет здоровье персонажа. Если здоровье падает до 0, он воскрешается.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        character.current_health = max(0, min(character.max_health, character.current_health + health_points))
        if character.current_health == 0:
            logging.info("Персонаж умер. Воскрешение...")
            return CharacterManager.revive_character(character_id)

        return update_object(character, Character.id, character_id)

    @staticmethod
    def change_money(character_id: int, amount: int) -> Character:
        """
        Изменяет количество денег у персонажа.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        character.money = max(0, character.money + amount)  # Не допускаем отрицательного баланса
        return update_object(character, Character.id, character_id)

    @staticmethod
    def increase_stat(character_id: int, stat_name: str, value: int) -> Character:
        """
        Увеличивает указанную характеристику на заданное значение.
        Проверяет допустимые границы изменения.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        if not hasattr(character, stat_name):
            raise ValueError(f"Характеристика {stat_name} не существует!")

        setattr(character, stat_name, max(1, getattr(character, stat_name) + value))
        return update_object(character, Character.id, character_id)

    @staticmethod
    def recalculate_dependent_stats(character_id: int) -> Character:
        """
        Пересчитывает параметры персонажа, зависящие от характеристик.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        character.max_health = character.level * 5 + 20 + character.strength * 5
        character.max_inventory_weight = character.strength * 10
        return update_object(character, Character.id, character_id)

    @staticmethod
    def level_up(character_id: int) -> Character:
        """
        Повышает уровень персонажа и пересчитывает связанные с этим характеристики.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        character.level += 1
        character.experience_points = 0
        return CharacterManager.recalculate_dependent_stats(character_id)

    @staticmethod
    def add_experience(character_id: int, experience: int) -> Character:
        """
        Добавляет опыт персонажу и повышает уровень при достижении лимита.
        """
        character = get_object(Character, Character.id, character_id)
        if not character:
            raise ValueError("Персонаж не найден!")

        character.experience_points += experience
        while character.experience_points >= character.level * 1000:
            character.experience_points -= character.level * 1000
            CharacterManager.level_up(character_id)

        return update_object(character, Character.id, character_id)

    @staticmethod
    def equip_item(user_id: int, item_id: int) -> bool:
        """
        Экипирует предмет из инвентаря, обновляя состояние персонажа.
        """
        item = get_object(Item, Item.id, item_id)
        character = get_object(Character, Character.user_id, user_id)

        if not item or not character:
            return False

        if item.category == "Weapon":
            if item.subcategory == "Melee Weapon":
                character.melee_weapon_id = item.id
            elif item.subcategory == "Ranged Weapon":
                if not character.range_weapon_1_id:
                    character.range_weapon_1_id = item.id
                else:
                    character.range_weapon_2_id = item.id
        elif item.category == "Armor":
            character.armor_id = item.id
        else:
            return False

        update_object(character, Character.id, character.id)
        return True

    @staticmethod
    def unequip_item(user_id: int, item_id: int) -> bool:
        """
        Снимает экипировку с персонажа.
        """
        character = get_object(Character, Character.user_id, user_id)
        if character.armor_id == item_id:
            character.armor_id = None
        elif character.range_weapon_1_id == item_id:
            character.range_weapon_1_id = None
        elif character.range_weapon_2_id == item_id:
            character.range_weapon_2_id = None
        update_object(character, Character.id, character.id)
        return True

    @staticmethod
    def check_item_requirements(character, item):
        logging.info(f"item: {item}")
        if item.type.lower() == "armor":
            item_data = get_object(Armor, Armor.id, item.id)
        elif item.type.lower() == "weapon":
            item_data = get_object(Weapon, Weapon.id, item.id)
        return (
                character.level >= item_data.min_level and
                character.strength >= item_data.min_strength and
                character.agility >= item_data.min_agility and
                character.intelligence >= item_data.min_intelligence
        )

from db.helper import get_item_with_subtype, get_object
from db.models import Item, Weapon, Armor, Consumable, Ammo


class ItemManager:

    @staticmethod
    def generate_item_stat_message(item_id):
        """
        Генерирует сообщение о характеристиках предмета по его ID.
        """
        item = get_object(Item, Item.id, item_id)
        if not item:
            return "❌ Предмет не найден."

        if item.type == "weapon":
            return ItemManager._format_weapon_message(item)
        elif item.type == "armor":
            return ItemManager._format_armor_message(item)
        elif item.type == "consumable":
            return ItemManager._format_consumable_message(item)
        elif item.type == "ammo":
            return ItemManager._format_ammo_message(item)
        else:
            return f"❌ Неизвестный тип предмета: {item.type}."

    @staticmethod
    def _format_common_fields(item, description):
        """
        Форматирует общие поля: название, описание, вес, цену.
        """
        message = f"🔹 **{item.name}**\n"
        message += f"📝 __{description}__\n\n"
        return message

    @staticmethod
    def _format_characteristics(characteristics):
        if characteristics:
            return "**Характеристики:**\n" + "\n".join(characteristics) + "\n\n"
        return ""

    @staticmethod
    def _format_requirements(requirements):
        if requirements:
            return "**Требования:**\n" + "\n".join(requirements) + "\n\n"
        return ""

    @staticmethod
    def _format_price_and_weight(item):
        return f"⚖️ {item.weight}, 💵 {item.base_price:,}".replace(",", " ")

    @staticmethod
    def _format_weapon_message(item: Item):
        weapon = get_object(Weapon, Weapon.id, item.id)
        message = ItemManager._format_common_fields(weapon, weapon.description)
        characteristics = []
        if weapon.physical_damage > 0:
            characteristics.append(f"💥 Физический урон: {weapon.physical_damage}")
        if weapon.energy_damage > 0:
            characteristics.append(f"⚡ Энергетический урон: {weapon.energy_damage}")
        if weapon.accuracy and weapon.weapon_type.lower() != "melee":
            characteristics.append(f"🎯 Точность: {weapon.accuracy}")
        if weapon.effective_range and weapon.weapon_type.lower() != "melee":
            characteristics.append(f"📏 Дальность: {weapon.effective_range}")
        message += ItemManager._format_characteristics(characteristics)

        requirements = []
        if weapon.min_level > 0:
            requirements.append(f"⭐️ Уровень: {weapon.min_level}")
        if weapon.min_strength > 0:
            requirements.append(f"💪 Сила: {weapon.min_strength}")
        if weapon.min_agility > 0:
            requirements.append(f"🏃 Ловкость: {weapon.min_agility}")
        if weapon.min_intelligence > 0:
            requirements.append(f"🧠 Интеллект: {weapon.min_intelligence}")
        message += ItemManager._format_requirements(requirements)

        actions = []
        if weapon.weapon_type.lower() == "melee":
            actions.append(f"- Удар: {weapon.ap_attack} ОД")
            actions.append(f"- Сильный удар: {weapon.ap_power_attack} ОД")
        elif weapon.weapon_type.lower() == "energy":
            actions.append(f"- Короткий луч: {weapon.ap_attack} ОД")
            if weapon.power_attack_ammo == 1:
                actions.append(f"- Короткий луч (прицельно): {weapon.ap_power_attack} ОД")
            elif weapon.power_attack_ammo > 1:
                actions.append(f"- Длинный луч: {weapon.ap_power_attack} ОД")
            actions.append(f"- Перезарядка: {weapon.ap_reload} ОД")
        elif weapon.weapon_type.lower() == "firearm":
            actions.append(f"- Одиночный выстрел: {weapon.ap_attack} ОД")
            if weapon.power_attack_ammo == 1:
                actions.append(f"- Прицельный выстрел: {weapon.ap_power_attack} ОД")
            elif weapon.power_attack_ammo > 1:
                actions.append(f"- Очередь: {weapon.ap_power_attack} ОД")
            actions.append(f"- Перезарядка: {weapon.ap_reload} ОД")
        if actions:
            message += "**Действия:**\n" + "\n".join(actions) + "\n"

        message += f"\n{ItemManager._format_price_and_weight(weapon)}"

        return message

    @staticmethod
    def _format_armor_message(item: Item):
        armor = get_object(Armor, Armor.id, item.id)
        message = ItemManager._format_common_fields(armor, armor.description)
        characteristics = []
        if armor.physical_defense > 0:
            characteristics.append(f"🛡️ Физическая защита: {armor.physical_defense}")
        if armor.energy_defense > 0:
            characteristics.append(f"🌌 Энергетическая защита: {armor.energy_defense}")
        if armor.chemical_defense > 0:
            characteristics.append(f"🧪 Химическая защита: {armor.chemical_defense}")
        message += ItemManager._format_characteristics(characteristics)

        requirements = []
        if armor.min_level > 0:
            requirements.append(f"⭐️ Уровень: {armor.min_level}")
        if armor.min_strength > 0:
            requirements.append(f"💪 Сила: {armor.min_strength}")
        if armor.min_agility > 0:
            requirements.append(f"🏃 Ловкость: {armor.min_agility}")
        if armor.min_intelligence > 0:
            requirements.append(f"🧠 Интеллект: {armor.min_intelligence}")
        message += ItemManager._format_requirements(requirements)

        message += f"\n{ItemManager._format_price_and_weight(armor)}"

        return message

    @staticmethod
    def _format_consumable_message(item: Item):
        consumable = get_object(Consumable, Consumable.id, item.id)
        message = ItemManager._format_common_fields(consumable, consumable.description)
        message += f"**Характеристики:**\n❤️ Восстановление HP: {consumable.heal}\n\n"
        message += "**Действия:**\n"
        message += f"- Использовать: {consumable.ap_use} ОД\n"
        message += f"\n{ItemManager._format_price_and_weight(consumable)}"
        return message

    @staticmethod
    def _format_ammo_message(item: Item):
        ammo = get_object(Ammo, Ammo.id, item.id)
        message = ItemManager._format_common_fields(ammo, ammo.description)
        characteristics = [f"📦 Тип боеприпасов: {ammo.ammo_type}"]
        if ammo.damage_modifier != 1.0:
            characteristics.append(f"⚙️ Модификатор урона: x{ammo.damage_modifier}")
        message += ItemManager._format_characteristics(characteristics)
        message += f"{ItemManager._format_price_and_weight(ammo)}"
        return message

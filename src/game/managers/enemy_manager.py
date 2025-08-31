from db.models import Enemy

class EnemyManager:
    @staticmethod
    def calculate_stats(enemy: Enemy, level):
        """
        Вычисляет и возвращает характеристики противника на основе его уровня.
        """
        if not isinstance(level, int) or level < 1:
            raise ValueError("Уровень врага должен быть положительным целым числом.")

        enemy.base_health = enemy.health_per_level * level

        enemy.base_physical_defense = enemy.physical_defense_per_level * level
        enemy.base_energy_defense = enemy.energy_defense_per_level * level
        enemy.base_chemical_defense = enemy.chemical_defense_per_level * level

        enemy.base_physical_damage = enemy.physical_damage_per_level * level
        enemy.base_energy_damage = enemy.energy_damage_per_level * level
        enemy.base_chemical_damage = enemy.chemical_damage_per_level * level

        return enemy
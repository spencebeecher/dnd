import math
import random
import numpy as np
import pandas as pd

# Dice Roll
def dr(num_dice, num_sides, num_simulations=2000):
    
    rolls = np.random.choice(num_sides, [num_simulations, num_dice]) + 1 
    return rolls.sum(axis=1).mean()

def difficulty_roll(difficulty_class, roll_modifier, advantage=False, disadvantage=False, 
    nat_20_wins=True, num_simulations=1000):
    res = []
    
    rolls = np.random.choice(20, num_simulations) + 1 

    extra_rolls = np.random.choice(20, num_simulations) +1 
    
    if advantage and not disadvantage:
        rolls = np.max([rolls, extra_rolls], axis=0)

    elif disadvantage and not advantage:
        rolls = np.min([rolls, extra_rolls], axis=0)

    
    return np.mean((rolls + roll_modifier > difficulty_class) | (rolls==20))


# Expected Damage on creature CR rating
# CR 0-3 : +5 to hit vs 13 AC requires an 8 or better; 65% to hit.
# CR 4 : (ASI) +6 to hit vs 14 AC requires an 8 or better; 65% to hit.
# CR 5-7 : (Proficiency +3) +7 to hit vs 15 AC requires an 8 or better; 65% to hit.
# CR 8 : (ASI to 20) +8 to hit vs 16 AC requires an 8 or better; 65% to hit.
# CR 9 : (Proficiency +4) +9 to hit vs 16 AC requires a 7 or better; 70% to hit.
# CR 10-12 : +9 to hit vs 17 AC requires an 8 or better; 65% to hit.
# CR 13-16 : (Proficiency +5) +10 to hit vs 18 AC requires an 8 or better; 65% to hit.
# CR 17+ : (Proficiency +6) +11 to hit vs 19 AC requires an 8 or better; 65% to hit.



def roll_damage(defender_AC=None, attack_modifier=None, damage_roll=None, bonus_damage=None, num_attacks=1, 
                    crit_added_damage=0, advantage_added_damage=0, crit_chance=0.05, crit_multiplier=2, 
                    advantage=False, disadvantage=False, num_simulations=1000, **extra_args):
    '''
    defender_AC: int  (default: 10) this is the AC of the defender and we model it as character level + 10
    attack_modifier: int — the 'to hit' modifier of the attacker
    damage_roll_damage: int — the expected dice damage of a single attack (eg. E[1d6] = 3.5)
    bonus_damage: int — additinal damage added to each attack (not doubled on crit)
    num_attacks: int — number of attacks per round
    crit_added_damage: int — additional damage added on crit (eg. smite)
    advantage_added_damage: int — additional damage added on advantage (eg. sneak attack)
    crit_chance: float — chance of crit (default: 0.05)
    crit_multiplier: float — multiplier on crit (default: 2)
    advantage: bool — whether the attack has advantage
    disadvantage: bool — whether the attack has disadvantage
    extra_args: dict — additional arguments to be passed to the function (eg. 'barbarian_lvl': 3) 
        the only import variables are character levels ending in '_lvl'
    '''


    if defender_AC is None:
        level = 10
        # estimate AC based on total level
        for arg in extra_args.keys():
            if '_lvl' in arg:
                level += extra_args[arg] 
        # https://rpg.stackexchange.com/questions/95624/average-ac-of-monsters-per-cr
        if level <= 3:
            defender_AC = 13
        elif level <= 4:
            defender_AC = 14
        elif level <= 7:
            defender_AC = 15
        elif level <= 9:
            defender_AC = 16
        elif level <= 12:
            defender_AC = 17
        elif level <= 16:
            defender_AC = 18
        else:
            defender_AC = 19

    probability_hit = difficulty_roll(defender_AC, attack_modifier, advantage=advantage, disadvantage=disadvantage,
        num_simulations=num_simulations)


    probability_hit = 1.0 - max(defender_AC -1 - attack_modifier, 0) / 20.0 

    if advantage and not disadvantage:
        #probability_hit = 1.0 - (1 - probability_hit) ** 2
        crit_chance = 1.0 - (1 - crit_chance) ** 2
        damage_roll += advantage_added_damage
    elif disadvantage and not advantage:
        #probability_hit = probability_hit ** 2
        crit_chance = crit_chance ** 2
    
    probability_hit_no_crit = max(0.0, probability_hit - crit_chance)
    
    crit_damage = (damage_roll + crit_added_damage) * crit_multiplier + bonus_damage
    non_crit_damage = damage_roll + bonus_damage
    expected_damage_per_hit = probability_hit_no_crit * non_crit_damage + crit_chance * crit_damage 

    results = {}
    results['probablity_hit'] = probability_hit
    results['defender_AC'] = defender_AC
    results['crit_chance per round'] = crit_chance * num_attacks
    results['hit damage'] = non_crit_damage
    results['crit damage'] = crit_damage
    results['expected damage per hit'] = expected_damage_per_hit
    results['expected damage per round'] = expected_damage_per_hit * num_attacks
    
    return results



def gambling_rolls(intimidation, deception, insight):
    bonus_array = np.array([intimidation, deception, insight])
    rolls = np.random.choice(20, size=3) + 1 + bonus_array

    # 3 separate rolls, each a 2d10 + 5
    opposing_rolls = (np.random.choice(10, size=(3,2)) + 1).sum(axis=1) + 5
    
    result = (rolls > opposing_rolls).sum()
    if result == 3:
        return 1
    elif result == 2:
        return 0.5
    elif result == 1:
        return -0.5
    else:
        return -2



def simulate_gambling_downtime(num_weeks, gamble_percent, intimidation, deception, insight, purse=1000, num_simulations=1000):

    results = []
    for _ in range(num_simulations):
        p = purse 
        for _ in range(num_weeks):
            g = p * gamble_percent
            p = p - g
            r = gambling_rolls(intimidation, deception, insight)
            p = p + g + r * g
        
        results.append(p)

    results = pd.Series(results)
    return results
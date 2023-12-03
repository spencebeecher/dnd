from io import StringIO
import math
import random
import numpy as np
import pandas as pd
from types import SimpleNamespace
import collections

class Abilities:
    def __init__(self, strength, dexterity, constitution, intelegence, wisdom, charisma):
        self.strength = strength
        self.dexterity = dexterity
        self.constitution = constitution
        self.intelegence = intelegence
        self.wisdom = wisdom 
        self.charisma = charisma

    def get(self):
        return dict(strength = self.strength,
        dexterity = self.dexterity,
        constitution = self.constitution,
        intelegence = self.intelegence,
        wisdom = self.wisdom ,
        charisma = self.charisma)

# https://rpgbot.net/dnd5/characters/fundamental_math/
_fundamental_math = pd.read_csv(StringIO("""Level_CR,Abl,Prof,Total,AC,Hit_Pcnt
1,3,2,5,13,65
2,3,2,5,13,65
3,3,2,5,13,65
4,4,2,6,14,65
5,4,3,7,15,65
6,4,3,7,15,65
7,4,3,7,15,65
8,5,3,8,16,65
9,5,4,9,16,70
10,5,4,9,17,65
11,5,4,9,17,65
12,5,4,9,17,65
13,5,5,10,18,65
14,5,5,10,18,65
15,5,5,10,18,65
16,5,5,10,18,65
17,5,6,11,19,65
18,5,6,11,19,65
19,5,6,11,19,65
20,5,6,11,19,65"""))

def fundamental_math():
    '''Fundamental assumptions on levels from https://rpgbot.net/dnd5/characters/fundamental_math/'''
    return _fundamental_math.copy()

# https://rpgbot.net/dnd5/characters/fundamental_math/
_damage_targets = pd.read_csv(StringIO("""Level_CR,Max Expected_HP,Low_DPR,Target_DPR,High_DPR,Dude_Stop,Warlock,TWF_Rogue
1,85,3.5,7.1,14.2,28.3,6.3,10.47
2,100,4.2,8.3,16.7,33.3,8.25,10.47
3,115,4.8,9.6,19.2,38.3,8.25,14.1
4,130,5.4,10.8,21.7,43.3,8.9,14.75
5,145,6,12.1,24.2,48.3,17.8,18.37
6,160,6.7,13.3,26.7,53.3,17.8,18.37
7,175,7.3,14.6,29.2,58.3,17.8,21.99
8,190,7.9,15.8,31.7,63.3,19.1,22.64
9,205,8.5,17.1,34.2,68.3,19.1,26.26
10,220,9.2,18.3,36.7,73.3,19.1,26.26
11,235,9.8,19.6,39.2,78.3,28.65,29.89
12,250,10.4,20.8,41.7,83.3,28.65,29.89
13,265,11,22.1,44.2,88.3,28.65,33.51
14,280,11.7,23.3,46.7,93.3,28.65,33.51
15,295,12.3,24.6,49.2,98.3,28.65,37.13
16,310,12.9,25.8,51.7,103.3,28.65,37.13
17,325,13.5,27.1,54.2,108.3,38.2,40.75
18,340,14.2,28.3,56.7,113.3,38.2,40.75
19,355,14.8,29.6,59.2,118.3,38.2,44.38
20,400,16.7,33.3,66.7,133.3,38.2,44.38
"""))
def damage_targets():
    '''Target damage for several scenarios from https://rpgbot.net/dnd5/characters/fundamental_math/'''
    return _damage_targets.copy()

def get_AC(level_or_CR):
    return fundamental_math().query(f"Level_CR=={level_or_CR}").AC.values[0]

def proficency_bonus(level_or_CR):
    return fundamental_math().query(f"Level_CR=={level_or_CR}").Prof.values[0]

def attack_bonus(level_or_CR):
    return fundamental_math().query(f"Level_CR=={level_or_CR}").Total.values[0]


class Dice:
    def __init__(self, num_dice, sides):
        
        self.num_dice=num_dice
        self.sides = sides

    def expectation(self):
        return (self.sides + 1.0) / 2.0 * self.num_dice 
    
    def roll(self, num_simulations=1):
        return np.random.choice(self.sides, (num_simulations, self.num_dice)).sum(axis=1) + self.num_dice 
    
    def __str__(self) -> str:
        return f'{self.num_dice}d{self.sides}'
    
    def __repr__(self) -> str:
        return f'{self.num_dice}d{self.sides}'
    
    def __add__(self, b):
        if type(b) == Dice:
            return DiceSet([self, b])
        elif type(b) == DiceSet:
            return DiceSet(b.die_array + [self])
        else:
            return None
    
    def __sub__(self, b):
        if type(b) == Dice:
            return DiceSet([self], [b])
        elif type(b) == DiceSet:
            return DiceSet([self], b.die_array)
        else:
            return None


def _colapse_dice(die_array):
    if not die_array:
        return None
    dice = collections.Counter()

    for d in die_array:
        dice[d.sides] += d.num_dice
    
    die_array = []
    for sides, num_dice in dice.items():
            die_array.append(Dice(num_dice, sides))
    return die_array

def _expectation(die_array):
    result = 0
    for d in die_array:
        result += d.expectation()
    return result
    
def _roll(die_array, num_simulations=1):
    result = []
    for d in die_array:
        result.append(d.roll(num_simulations))
    return np.array(result).sum(axis=0)

class DiceSet:

    def __init__(self, die_array, negative_die_array=None):
        self.die_array = _colapse_dice(die_array)
        self.negative_die_array = _colapse_dice(negative_die_array)
             
    
    def expectation(self):
        if self.negative_die_array:
            return _expectation(self.die_array) - _expectation(self.negative_die_array)
        else:
            return _expectation(self.die_array)
    
    def roll(self, num_simulations=1):
        if self.negative_die_array:
            return _roll(self.die_array, num_simulations) - _roll(self.negative_die_array, num_simulations)
        else:
            return _roll(self.die_array, num_simulations)
    

    def __add__(self, b):
        if type(b) == Dice:
            return DiceSet([b] + self.die_array, self.negative_die_array)
        elif type(b) == DiceSet:
            return DiceSet(b.die_array + self.die_array,  b.negative_die_array + self.negative_die_array)
        else:
            return None
        
    def __sub__(self, b):
        if type(b) == Dice:
            return DiceSet(self.die_array, [b] + self.negative_die_array)
        elif type(b) == DiceSet:
            return DiceSet(b.negative_die_array + self.die_array, b.die_array + self.negative_die_array)
        else:
            return None
        
    def __str__(self) -> str:
        if self.negative_die_array:
            return f'{self.die_array} - {self.negative_die_array}'
        else:
            return f'{self.die_array}'
    
    def __repr__(self) -> str:
        return self.__str__()

def advantage_roll(advantage=False, disadvantage=False, num_simulations=1):
    
    rolls = Dice(1,20).roll(num_simulations)
    
    if not disadvantage:
        for _ in range(advantage):
            extra_rolls = Dice(1,20).roll(num_simulations)
            rolls = np.max([rolls, extra_rolls], axis=0)

    elif not advantage:
        extra_rolls = Dice(1,20).roll(num_simulations)
        rolls = np.min([rolls, extra_rolls], axis=0)
    
    return rolls



def spell_save_attack(save_modifier, save_dc, damage_dice = None, save_damage_dice = None, save_advantage=False, 
               save_disadvantage=False, num_simulations=10000):
    
    rolls = advantage_roll(advantage=save_advantage, disadvantage=save_disadvantage, num_simulations=num_simulations)
    
    if damage_dice:
        if save_damage_dice:
            return (~ ((rolls + save_modifier >= save_dc) | (rolls==20))) * damage_dice.roll(num_simulations) + \
                (rolls + save_modifier < save_dc) * save_damage_dice.roll(num_simulations)
        else:
            return (~ (rolls + save_modifier >= save_dc)) * damage_dice.roll(num_simulations) 
    else:
        return (~ (rolls + save_modifier >= save_dc)  | (rolls==20)) 



def roll_damage(defender_AC, attack_modifier, damage_dice, bonus_damage=0, 
                    crit_added_damage_dice=None, crit_on=20,  
                    advantage=False, disadvantage=False, num_simulations=10000):
    '''
    defender_AC: int  (default: 10) this is the AC of the defender and we model it as character level + 10
    attack_modifier: int — the 'to hit' modifier of the attacker
    damage_dice: int — the expected dice damage of a single attack (eg. E[1d6] = 3.5)
    bonus_damage: int — additinal damage added to each attack (not doubled on crit)
    crit_added_damage: int — additional damage added on crit (eg. smite)
    crit_on: int — crit on rolls equal to or greater than {crit_on}
    advantage: bool or int — numper of times to roll advantage dice. defauts to zero.
    disadvantage: bool — whether the attack has disadvantage
    '''
    # https://rpgbot.net/dnd5/characters/fundamental_math/
    attack_rolls = advantage_roll(advantage=advantage, disadvantage=disadvantage, num_simulations=num_simulations)

    crits = attack_rolls >= crit_on
    hits = (attack_rolls + attack_modifier >= defender_AC) | crits

    damage_roll = damage_dice.roll(num_simulations)

    if crit_added_damage_dice:
        damage_roll += (damage_roll + crit_added_damage_dice.roll(num_simulations)) * crits 
    else:
        damage_roll += (damage_roll) * crits

    return (damage_roll + bonus_damage) * hits




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
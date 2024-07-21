from importlib import reload
import matplotlib.pyplot as plt
import dnd

from dnd import Dice

import pandas as pd
import numpy as np
import json
import os

def read_creatures():
    creatures = []
    path = 'data/bestiary/'
    for filename in os.listdir(path):
        if filename.endswith('.json'):
            with open(path + filename, 'r') as f:
                j = json.load(f)
                if 'monster' in j:
                    for monster_json in j['monster']:
                        is_npc = 'isNpc' in monster_json and monster_json['isNpc']
                        is_copy = '_copy' in monster_json 
                        is_summoned = 'summonedBySpell' in monster_json or 'summonedByClass' in monster_json
                        
                        if not is_npc and not is_copy and not is_summoned:
                            creature = Creature(monster_json)
                            creatures.append(creature)
    return creatures

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            try:
                v = float(v)
            except:
                pass
            items.append((new_key, v))
    return dict(items)

def dict_vals_to_float(d):
    return dict( (k, float(v)) for k, v in d.items() )

# turn a list of strings into a dictionary of boolean true values
def list_to_dict(l, sep='_', parent_key=''):
	return {f'{parent_key}{sep}{x}': True for x in l if type(x) == str}

import re
level_regex = re.compile('(\d+)')
fractionlevel_regex = re.compile('(\d+)/(\d+)')
def parse_level(value):
    if type(value) == int or type(value) == float:
        return value
    level_match = level_regex.match(value)
    fraction_match = fractionlevel_regex.match(value)
    if fraction_match:
        
        numerator = float(fraction_match.group(1))
        denominator = float(fraction_match.group(2))
        return numerator / denominator
    if level_match:
        return float(level_match.group(1))
        
    
    return np.nan

class Creature:
    def __init__(self, creature_dict):
        # initialize values from dictionary
        self.creature_dict = creature_dict

    def as_record(self):
        # return a flattened dictionary recursively
        ret = flatten_dict(self.creature_dict)
        if 'cr' in ret:
            ret['cr'] = parse_level(ret['cr'])
        if 'ac' in ret:
            if type(ret['ac'][0]) == dict:
                ret['ac_val'] = ret['ac'][0]['ac']
            elif type(ret['ac'][0]) == int:
                ret['ac_val'] = ret['ac'][0]
        if 'immune' in ret:
            ret.update(list_to_dict(ret['immune'], parent_key='immune'))
        if 'resist' in ret:
            resist_ret = list_to_dict(ret['resist'], parent_key='resist')
            if 'resist' in ret:
                for v in ret['resist']:
                    if type(v) == dict and 'resist' in v:
                        resist_ret.update(list_to_dict(v['resist'], parent_key='resist'))
            ret.update(resist_ret)
        if 'conditionImmune' in ret:
            ret.update(list_to_dict(ret['conditionImmune'], parent_key='conditionImmune'))
        return ret
    

attributes = ['cha', 'con', 'dex', 'int', 'str', 'wis']
skll_to_attributes = {
    'acrobatics': 'dex',
    'animal handling': 'wis',
    'arcana': 'int',
    'athletics': 'str',
    'deception': 'cha',
    'history': 'int',
    'insight': 'wis',
    'intimidation': 'cha',
    'investigation': 'int',
    'medicine': 'wis',
    'nature': 'int',
    'perception': 'wis',
    'performance': 'cha',
    'persuasion': 'cha',
    'religion': 'int',
    'sleight of hand': 'dex',
    'stealth': 'dex',
    'survival': 'wis'
}

def fill_columnset_default(df, column_prefix, default):
    for column in df.columns:
        if column.startswith(column_prefix):
            df[column] = df[column].fillna(default)
    return df

def get_creatures_df():
    creatures = read_creatures()
    creatures_df = pd.DataFrame([c.as_record() for c in creatures])
    creatures_df = creatures_df[creatures_df['cr'].isna() == False].reset_index(drop=True)
    for attribute in attributes:
        creatures_df['save_'+attribute] = np.where(
            creatures_df['save_'+attribute] > np.round((creatures_df[attribute] - 10)/2), 
            creatures_df['save_'+attribute], 
            np.round((creatures_df[attribute] - 10)/2)
        )

    for skill in skll_to_attributes:
        creatures_df['skill_'+skill] = np.where(
            creatures_df['skill_'+skill] > np.round((creatures_df[skll_to_attributes[skill]] - 10)/2), 
            creatures_df[skll_to_attributes[skill]], 
            np.round((creatures_df[skll_to_attributes[skill]] - 10)/2)
        )

    for col in ['immune', 'conditionImmune', 'resist', 'vulnerable']:
        fill_columnset_default(creatures_df, col+'_', False)
    

    return creatures_df



import dnd
def creature_damage_save(c, save_type, save_dc, damage_dice, damage_type):
    modifier = 1
    if c[f'resist_{damage_type}']:
        modifier = 0.5
    elif c[f'immune_{damage_type}']:
        modifier = 0 
    
    return dnd.save_roll(c[f'save_{save_type}'], save_dc, damage_dice, 0.5*damage_dice).mean()*modifier

def creature_condition_save(c, save_type, save_dc, condition):
    modifier = 1
    if f'conditionImmune_{condition}' in c and c[f'conditionImmune_{condition}']:
        #print(c['name'], 'immune', c[f'conditionImmune_{condition}'])
        modifier = 0
    return dnd.save_roll(c[f'save_{save_type}'], save_dc).mean()*modifier

def get_resistance_stats(df, resistance):
    pivot_cols = ['cr', f'resist_{resistance}', f'immune_{resistance}']
    p_df = pd.DataFrame(df.groupby(pivot_cols).name.count()).pivot_table(index=pivot_cols[0], columns=pivot_cols[1:], values='name', fill_value=0)
    p_df.columns = ['No Resistance', resistance + ' Resistance', resistance + ' Immunity']
    p_df.plot(kind='bar', stacked=True)
    plt.title(resistance + ' Resistance and Immunity by Challenge Level')
    p_df['percent_immune'] = p_df[resistance + ' Immunity'] / (p_df[resistance + ' Immunity'] + p_df[resistance + ' Resistance'] + p_df['No Resistance']) 
    p_df['percent_resistant'] = p_df[resistance + ' Resistance'] / (p_df[resistance + ' Immunity'] + p_df[resistance + ' Resistance'] + p_df['No Resistance'])
    p_df['percent_no_resistance'] = p_df['No Resistance'] / (p_df[resistance + ' Immunity'] + p_df[resistance + ' Resistance'] + p_df['No Resistance'])
    return p_df

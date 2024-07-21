import re
import pandas as pd
import numpy as np

immunities = ['poison', 'fire', 'cold', 'lightning', 'bludgeoning', 'piercing', 'slashing', 'acid', 'necrotic', 'radiant', 
              'thunder', 'force', 'psychic',
              'slashing', 'bludgeoning', 'piercing']

conditions = {
'prone' : 'prone',
'blind' : 'blindness',
 'blinded' : 'blindness',
 'blindness': 'blindness',
'charmed' : 'charmed',
 'confusion': 'confusion',
'deafeed' : 'deafened',
 'deafened': 'deafened',
'exhausted': 'exhaustion',
 'exhaustion' : 'exhaustion',
'fright': 'frighened',
 'frightened' : 'frightened',
'grappled' : 'grappled',
'paralysis' : 'paralysis',
 'paralyzed' : 'paralysis',
 'petrification' : 'petrified',
 'petrified' : 'petrified',
'poisoned': 'poisoned',
'restrained' : 'restrained',
'stunned' : 'stunned',
'unconscious' : 'unconscious'
}

removed = set()
def map_immunities(value):
    
    if value == np.nan or type(value) != str:
        return []
    im=list([x for x in re.split('[,; "]+', value) if x != '' ])
    
    for a in im:
        if a not in immunities:
            removed.add(a)
    
    return list([x for x in im if x in immunities])

def map_condition_immunities(value):
    if value == np.nan or type(value) != str:
        return []
    im=list([x for x in re.split('[,; "]+', value) if x != '' ])
    for a in im:
        if a not in conditions:
            removed.add(a)
        

    return list([conditions[x] for x in im if x in conditions])



class Creature():
    
    def __init__(self, lines):
        


        comment_counter = 0
        for line in lines:
            if line.startswith('---'):
                comment_counter += 1
                if comment_counter == 2:
                    break
            else:
                try:
                    line = line.lower()

                    
                    parse_line = lambda x: x.split(': ')[1].strip()

                    parse_string = lambda x: x.split(': ')[1].strip().removeprefix('"').removesuffix('"')

                    parse_first_val = lambda x: int(x.split(': ')[1].split(' ')[0].strip())
                    parse_attribute = parse_first_val

                    parse_first_quote = lambda x: int(x.split(': ')[1].split(' ')[0].strip().removeprefix('"').removesuffix('"'))

                    parse_tags = lambda x: list([y for y in x.split(': ')[1].strip().removeprefix('[').removesuffix(']').split(',')])

                    
                    if line.startswith('name:'):
                        self.name = parse_string(line)
                    elif line.startswith('tags:'):
                        self.tags = parse_tags(line)
                    elif line.startswith('cha:'):
                        self.cha = parse_attribute(line)
                    elif line.startswith('wis:'):
                        self.wis = parse_attribute(line)
                    elif line.startswith('int:'):
                        self.int = parse_attribute(line)
                    elif line.startswith('con:'):
                        self.con = parse_attribute(line)
                    elif line.startswith('dex:'):
                        self.dex = parse_attribute(line)
                    elif line.startswith('str:'):
                        self.str = parse_attribute(line)
                    elif line.startswith('size:'):
                        s = line.split(': ')[1].strip()
                        s = s.split(' ')
                        self.size = s[0]
                        self.type = s[1]
                        self.full_type = ' '.join(s[1:])
                    elif line.startswith('alignment:'):
                        self.alignment = line.split(': ')[1].strip()
                    elif line.startswith('challenge:'):
                        self.challenge = parse_string(line)
                    elif line.startswith('languages:'):
                        self.languages = line.split(': ')[1].strip()
                    elif line.startswith('skills:'):
                        self.skills = line.split(': ')[1].strip()
                    elif line.startswith('speed:'):
                        self.speed = parse_line(line)
                    elif line.startswith('hit_points:'):
                        self.hit_points = parse_first_quote(line)
                    elif line.startswith('armor_class:'):
                        self.armor_class = parse_first_quote(line)
                    elif line.startswith('page_number:'):
                        self.page_number = parse_first_val(line)
                    elif line.startswith('senses:'):
                        self.senses = parse_line(line)
                    elif line.startswith('damage_resistances:'):
                        self.damage_resistances = map_immunities(parse_line(line))
                    elif line.startswith('layout:'):
                        pass
                    elif line.startswith('saving_throws:'):
                        self.saving_throws = parse_line(line)
                    elif line.startswith('damage_immunities:'):
                        self.damage_immunities = map_immunities(parse_line(line))
                    elif line.startswith('condition_immunities:'):
                        self.condition_immunities = map_condition_immunities(parse_line(line))
                    elif line.startswith('damage_vulnerabilities:') or line.startswith('damage_vulnerabilites:'):
                        self.damage_vulnerabilities = map_immunities(parse_line(line))

                        
                    else:
                        print(f'{self.name} Unparsed line: {line}')
                except:
                    print('error', line)
                    
                    print(self)

    def __str__(self):
        return str(vars(self))
    

    #look through all md files in the creatures directory reading each in
#and parsing the data into a pandas dataframe
import os



def read_creatures():
    creatures = []
    for filename in os.listdir('creatures'):
        if filename.endswith('.md'):
            with open('creatures/' + filename, 'r') as f:
                creature = Creature(f.readlines())
                creatures.append(creature)
                
    return creatures

creatures = read_creatures()

#Create a pandas dataframe from the creatures
creatures = pd.DataFrame([c.__dict__ for c in creatures])

import re
level_regex = re.compile('(\d+) .+')
fractionlevel_regex = re.compile('(\d+)/(\d+) .+')
def parse_level(value):
    level_match = level_regex.match(value)
    if level_match:
        return float(level_match.group(1))
    else:
        fraction_match = fractionlevel_regex.match(value)
        if fraction_match:
            numerator = float(fraction_match.group(1))
            denominator = float(fraction_match.group(2))
            return numerator / denominator
    return np.nan

creatures['challenge_level'] = creatures.challenge.astype(str).apply(parse_level)

# get all the unique tags in a column of a dataframe that is a list
def get_tags(df, column):
    tags = set()
    for tag_list in df[column].dropna():
        tags.update(tag_list)
    return tags

#turn a list of values into a dataframe of boolean values
# and the values are in the column
def list_to_df(df, column, in_place=False):
    if not in_place:
        df = df.copy()
    values = get_tags(df, column)
    for value in values:
        df[f'{column}_{value}'] = df[column].apply(lambda x: value in x if type(x) == list else False)
    return df

creatures = list_to_df(creatures, 'damage_immunities')
creatures = list_to_df(creatures, 'damage_resistances')
creatures = list_to_df(creatures, 'damage_vulnerabilities')
creatures = list_to_df(creatures, 'condition_immunities')


import re

save_regex = re.compile('.*?(\w+).*?\+(\d+).*?')

def parse_save(value):
    ret = {}
    for save in value.split(','):
        save_match = save_regex.match(save)
        if save_match:
            ret[save_match.group(1)[:3]] = int(save_match.group(2))
    return ret


saves = pd.DataFrame.from_records(creatures['saving_throws'].astype(str).apply(parse_save)).fillna(0)

for save in saves.columns:
    #save = save[:3]
    creatures['saving_throws_'+save] = np.where(saves[save] > np.round((creatures[save] - 10)/2), saves[save], np.round((creatures[save] - 10)/2))

import dnd
def creature_damage_save(c, save_type, save_dc, damage_dice, damage_type):
    modifier = 1
    if c[f'damage_resistances_{damage_type}']:
        modifier = 0.5
    elif c[f'damage_immunities_{damage_type}']:
        modifier = 0 
    
    return dnd.save_roll(c[f'saving_throws_{save_type}'], save_dc, damage_dice, 0.5*damage_dice).mean()*modifier

def creature_condition_save(c, save_type, save_dc, condition):
    modifier = 1
    if f'condition_immunities_{condition}' in c and c[f'condition_immunities_{condition}']:
        modifier = 0
    return dnd.save_roll(c[f'saving_throws_{save_type}'], save_dc).mean()*modifier
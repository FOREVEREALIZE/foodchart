import json
from typing import Iterable, Sequence, Tuple, Union, Optional

MATERIAL_EXCEL = []
ITEM_ABILITIES = []
BUFF_EXCEL = []
TEXT_MAP = {}

def get_ability(ability_name, modifier):
    for ability in ITEM_ABILITIES:
        if ability['Default'].get('abilityName', "") == ability_name:
            return ability['Default'], ability['Default']['modifiers'].get(modifier)
    
    return None, None

def get_buff(server_buff_id):
    for buff in BUFF_EXCEL:
        if str(buff['serverBuffId']) == server_buff_id:
            return buff
    
    return None

def get_material(material_id):
    for material in MATERIAL_EXCEL:
        if material['id'] == material_id:
            return material
    
    return None

def get_buff_modifier(server_buff_id):
    buff = get_buff(server_buff_id)
    if not buff:
        return None, None, None
    
    group, modifier = get_ability(buff['abilityName'], buff['modifierName'])
    return buff, group, modifier


def get_value_from_overrides(overrides, key, default=0):
    """Get a value from the overrides map or return default."""
    return overrides.get(key, default)

def process_fkcdopoiode_action(action, overrides):
    """
    Process FKCDOPOIODE actions that set override values.
    These can set values directly or perform operations like ADD.
    """
    ratio = action.get('ratio')
    override_key = action.get('overrideMapKey')
    
    if not override_key:
        return
    
    # Handle array form: [key, value, operation]
    if isinstance(ratio, list) and len(ratio) >= 2:
        source_key = ratio[0]
        value = ratio[1]
        operation = ratio[2] if len(ratio) > 2 else None
        
        if operation == "ADD":
            current = overrides.get(source_key, 0)
            overrides[override_key] = current + value
        else:
            overrides[override_key] = value
    else:
        # Direct value assignment
        overrides[override_key] = ratio

def process_chance_tree(effect, overrides, base_probability=1.0):
    """
    Recursively process chance-based effects (DKBEECBMHLO).
    Returns a list of (probability, percent, fixed) tuples.
    """
    if effect.get('$type') != 'DKBEECBMHLO':
        return []
    
    chance = effect.get('chance', 1.0)
    outcomes = []
    
    # Process success actions
    success_actions = effect.get('successActions', [])
    if success_actions:
        success_overrides = overrides.copy()
        for action in success_actions:
            if action.get('$type') == 'FKCDOPOIODE':
                process_fkcdopoiode_action(action, success_overrides)
        
        outcomes.append((base_probability * chance, success_overrides))
    
    # Process fail actions (recursively for nested chances)
    fail_actions = effect.get('failActions', [])
    if fail_actions:
        for action in fail_actions:
            if action.get('$type') == 'DKBEECBMHLO':
                # Nested chance
                nested_outcomes = process_chance_tree(action, overrides.copy(), base_probability * (1 - chance))
                outcomes.extend(nested_outcomes)
            elif action.get('$type') == 'FKCDOPOIODE':
                # Direct action on failure
                fail_overrides = overrides.copy()
                process_fkcdopoiode_action(action, fail_overrides)
                outcomes.append((base_probability * (1 - chance), fail_overrides))
    else:
        # No fail actions means base values on failure
        outcomes.append((base_probability * (1 - chance), overrides.copy()))
    
    return outcomes

def calculate_heal_amount(total_time, group, modifier):
    """
    Calculate healing amount from a modifier.
    Returns either:
    - (percent, fixed) for instant abilities
    - {'type': 'timed', 'base': {...}, 'steps': [...]} for timed abilities
    - {'type': 'chance', 'outcomes': [(probability, percent, fixed), ...]} for chance-based abilities
    """
    # Handle abilities without group (direct modifiers)
    if not group:
        group = {'abilitySpecials': {}}
    
    def resolve_value(value, overrides):
        """Resolve a value which can be a number, string key, or override key."""
        if isinstance(value, str):
            # Check overrides first, then ability specials
            if value in overrides:
                return overrides[value]
            return group['abilitySpecials'].get(value, 0)
        return value
    
    # Initialize override map with base values
    overrides = {}
    
    # First pass: process FKCDOPOIODE actions to set up base overrides
    for effect in modifier.get('onAdded', []):
        if effect.get('$type') == 'FKCDOPOIODE':
            process_fkcdopoiode_action(effect, overrides)
    
    # Check if this is a chance-based ability
    has_chance = any(effect.get('$type') == 'DKBEECBMHLO' for effect in modifier.get('onAdded', []))
    
    # Check if this is a timed ability
    is_timed = 'onThinkInterval' in modifier and len(modifier.get('onThinkInterval', [])) > 0
    
    if has_chance:
        # Process chance tree to get all possible outcomes
        all_outcomes = []
        for effect in modifier.get('onAdded', []):
            if effect.get('$type') == 'DKBEECBMHLO':
                outcomes = process_chance_tree(effect, overrides.copy())
                all_outcomes.extend(outcomes)
        
        # Calculate healing for each outcome
        outcome_results = []
        for probability, outcome_overrides in all_outcomes:
            outcome_percent = 0
            outcome_fixed = 0
            
            # Sum up all heal actions (JMEOFOGONAK) with these overrides
            for effect in modifier.get('onAdded', []):
                if effect.get('$type') == 'JMEOFOGONAK':
                    pct = resolve_value(effect.get('OJBDHICLDEM', 0), outcome_overrides)
                    fixed = resolve_value(effect.get('BOLMBKLPOKN', 0), outcome_overrides)
                    outcome_percent += pct
                    outcome_fixed += fixed
            
            # Handle timed healing for this outcome
            for effect in modifier.get('onThinkInterval', []):
                if effect.get('$type') == 'JMEOFOGONAK':
                    ticks = total_time // modifier.get('thinkInterval', 1) if 'thinkInterval' in modifier else 0
                    outcome_percent += resolve_value(effect.get('OJBDHICLDEM', 0), outcome_overrides) * ticks
                    outcome_fixed += resolve_value(effect.get('BOLMBKLPOKN', 0), outcome_overrides) * ticks
            
            outcome_results.append((probability, outcome_percent, outcome_fixed))
        
        return {'type': 'chance', 'outcomes': outcome_results}
    elif is_timed:
        # Timed ability - calculate base and progressive steps
        base_percent = 0
        base_fixed = 0
        
        # Get base healing from onAdded
        for effect in modifier.get('onAdded', []):
            if effect.get('$type') == 'JMEOFOGONAK':
                base_percent += resolve_value(effect.get('OJBDHICLDEM', 0), overrides)
                base_fixed += resolve_value(effect.get('BOLMBKLPOKN', 0), overrides)
        
        # Get per-tick healing from onThinkInterval
        tick_percent = 0
        tick_fixed = 0
        for effect in modifier.get('onThinkInterval', []):
            if effect.get('$type') == 'JMEOFOGONAK':
                tick_percent += resolve_value(effect.get('OJBDHICLDEM', 0), overrides)
                tick_fixed += resolve_value(effect.get('BOLMBKLPOKN', 0), overrides)
        
        # Calculate progressive steps
        think_interval = modifier.get('thinkInterval', 1)
        num_ticks = int(total_time // think_interval) if think_interval > 0 else 0
        
        steps = []
        for tick in range(1, num_ticks + 1):
            steps.append({
                'tick': tick,
                'time': tick * think_interval,
                'percent': base_percent + (tick_percent * tick),
                'fixed': base_fixed + (tick_fixed * tick)
            })
        
        return {
            'type': 'timed',
            'base': {
                'percent': base_percent,
                'fixed': base_fixed
            },
            'per_tick': {
                'percent': tick_percent,
                'fixed': tick_fixed
            },
            'interval': think_interval,
            'duration': total_time,
            'steps': steps
        }
    else:
        # Instant ability - just sum up all healing effects
        total_percent = 0
        total_fixed = 0
        
        for effect in modifier.get('onAdded', []):
            if effect.get('$type') == 'JMEOFOGONAK':
                total_percent += resolve_value(effect.get('OJBDHICLDEM', 0), overrides)
                total_fixed += resolve_value(effect.get('BOLMBKLPOKN', 0), overrides)
        
        return total_percent, total_fixed

def export(data):
    """Export food healing data to JSON file."""
    with open("data.json", 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def main():
    global MATERIAL_EXCEL, ITEM_ABILITIES, BUFF_EXCEL

    # /ExcelBinOutput/MaterialExcelConfigData.json
    with open('./MaterialExcelConfigData.json', 'r', encoding='utf-8') as f:
        MATERIAL_EXCEL = json.load(f)
    
    # /ExcelBinOutput/BuffExcelConfigData.json
    with open('./BuffExcelConfigData.json', 'r', encoding='utf-8') as f:
        BUFF_EXCEL = json.load(f)
    
    # /BinOutput/Ability/Temp/ItemAbilities.json
    with open('./ItemAbilities.json', 'r', encoding='utf-8') as f:
        ITEM_ABILITIES = json.load(f)
    
    # /TextMap/TextMapEN.json
    with open('./TextMapEN.json', 'r', encoding='utf-8') as f:
        TEXT_MAP = json.load(f)

    data = []
    revival_data = []
    
    for material in MATERIAL_EXCEL:
        # if material['foodQuality'] in ['FOOD_QUALITY_DELICIOUS', 'FOOD_QUALITY_STRANGE', 'FOOD_QUALITY_ORDINARY']:
        if any(use.get('useOp') == 'ITEM_USE_ADD_SERVER_BUFF' for use in material.get('itemUse', [])):
            # Check if this is a revival food
            is_revival = any(use.get('useOp') == 'ITEM_USE_RELIVE_AVATAR' for use in material.get('itemUse', []))
            
            # Find the ITEM_USE_ADD_SERVER_BUFF entry
            server_buff_id = None
            for use in material.get('itemUse', []):
                if use.get('useOp') == 'ITEM_USE_ADD_SERVER_BUFF':
                    server_buff_id = use['useParam'][0]
                    break
            
            if not server_buff_id:
                continue
            
            buff, group, buff_modifier = get_buff_modifier(server_buff_id)
            if buff_modifier:
                # food_type = "instant"
                # if "onAdded" not in buff_modifier:
                #     continue

                # if "onThinkInterval" in buff_modifier and len(buff_modifier.get('onThinkInterval', [])) > 0:
                #     food_type = "timed"

                heal_result = calculate_heal_amount((buff or {}).get('time', 0), group, buff_modifier)
                
                food_entry = {
                    'id': material['id'],
                    'name': TEXT_MAP.get(str(material['nameTextMapHash']), f"UNK_{material['nameTextMapHash']}"),
                    'stars': material['rankLevel'],
                    'quality': material.get('foodQuality', ""),
                    # 'type': food_type
                }
                
                # Check if it's a chance-based result
                if isinstance(heal_result, dict) and heal_result.get('type') == 'chance':
                    food_entry['healing'] = {
                        'type': 'chance',
                        'outcomes': [
                            {
                                'probability': prob,
                                'percent': pct * 100,
                                'fixed': fix
                            }
                            for prob, pct, fix in heal_result['outcomes']
                        ]
                    }
                    # Calculate expected values for logging
                    expected_pct = sum(prob * pct for prob, pct, _ in heal_result['outcomes'])
                    expected_fix = sum(prob * fix for prob, _, fix in heal_result['outcomes'])
                    print(f"{material['id']}: CHANCE - Expected: {expected_pct * 100:.0f}% + {expected_fix:.0f}")
                elif isinstance(heal_result, dict) and heal_result.get('type') == 'timed':
                    food_entry['healing'] = {
                        'type': 'timed',
                        'base': {
                            'percent': heal_result['base']['percent'] * 100,
                            'fixed': heal_result['base']['fixed']
                        },
                        'per_tick': {
                            'percent': heal_result['per_tick']['percent'] * 100,
                            'fixed': heal_result['per_tick']['fixed']
                        },
                        'interval': heal_result['interval'],
                        'duration': heal_result['duration'],
                        'steps': [
                            {
                                'tick': step['tick'],
                                'time': step['time'],
                                'percent': step['percent'] * 100,
                                'fixed': step['fixed']
                            }
                            for step in heal_result['steps']
                        ]
                    }
                    # Calculate total healing for logging
                    # if heal_result['steps']:
                    #     last_step = heal_result['steps'][-1]
                    #     # print(f"{material['id']}: ({food_entry.healing.get('type')}) {last_step['percent'] * 100:.0f}% + {last_step['fixed']:.0f} over {heal_result['duration']}s")
                    # else:
                    #     pass
                    #     # print(f"{material['id']}: ({food_type}) No ticks")
                else:
                    heal_pct, heal_fix = heal_result
                    food_entry['healing'] = {
                        'type': 'instant',
                        'percent': heal_pct * 100,
                        'fixed': heal_fix
                    }
                    # print(f"{material['id']}: ({food_type}) {heal_pct * 100:.0f}% + {heal_fix:.0f}")
                
                # Add to appropriate array based on whether it's a revival food
                if is_revival:
                    revival_data.append(food_entry)
                else:
                    data.append(food_entry)

    export({ "healing": data, "revival": revival_data })

if __name__ == "__main__":
    main()

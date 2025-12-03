"""
Troop Trait Mappings for Merge Tactics (December 2025)

Each troop has:
- Primary Trait (Origin): Ace, Clan, Giant, Goblin, Noble, P.E.K.K.A, Undead
- Secondary Trait (Role): Assassin, Blaster, Brawler, Brutalist, Ranger, Superstar, Thrower

Note: Some troops are rotated out in December 2025 season but are kept in this mapping
for historical data and future rotations.
"""

# Complete mapping of all troops to their traits
# Format: troop_name: (primary_trait, secondary_trait, is_rotated_out)
TROOP_TRAITS = {
    # Index 0-4
    "archer": ("Clan", "Ranger", True),  # ROTATED OUT Dec 2025
    "archer_queen": ("Clan", "Ranger", False),  # Changed from Avenger to Ranger
    "baby_dragon": ("Fire", "Mage", True),  # ROTATED OUT Dec 2025 (Fire/Mage traits also rotated)
    "bandit": ("Ace", "Assassin", False),  # Changed from Avenger to Assassin
    "barbarian": ("Clan", "Brawler", False),

    # Index 5-9
    "dart_goblin": ("Goblin", "Ranger", False),
    "e_wiz": ("Electric", "Mage", True),  # ROTATED OUT Dec 2025 (Electric/Mage traits also rotated)
    "electro_giant": ("Giant", "Superstar", False),  # Active - traits updated to Giant/Superstar
    "executioner": ("Ace", "Thrower", False),
    "giant_skeleton": ("Undead", "Brawler", True),  # ROTATED OUT Dec 2025

    # Index 10-14
    "goblin": ("Goblin", "Assassin", False),
    "goblin_machine": ("Goblin", "Brutalist", False),  # Changed from Juggernaut to Brutalist
    "golden_knight": ("Noble", "Assassin", False),
    "knight": ("Noble", "Juggernaut", True),  # ROTATED OUT Dec 2025 (Juggernaut trait also rotated)
    "mega_knight": ("Ace", "Brawler", False),

    # Index 15-19
    "mini_pekka": ("P.E.K.K.A", "Brutalist", False),  # NEW Dec 2025
    "monk": ("Ace", "Superstar", False),  # NEW Dec 2025
    "musketeer": ("Clan", "Superstar", False),  # Changed from Blaster to Superstar (Clan inferred)
    "pekka": ("P.E.K.K.A", "Brawler", False),  # Changed from Ace/Avenger to P.E.K.K.A/Brawler
    "prince": ("Noble", "Brawler", False),

    # Index 20-24
    "princess": ("Noble", "Blaster", False),  # Changed from Ranger to Blaster
    "royal_ghost": ("Undead", "Assassin", False),
    "royal_giant": ("Giant", "Ranger", False),  # NEW Dec 2025
    # "skeleton": removed - spawned unit, not purchasable
    "skeleton_dragon": ("Undead", "Ranger", False),

    # Index 25-29
    "skeleton_king": ("Undead", "Brutalist", False),  # Changed from Juggernaut to Brutalist
    "spear_goblin": ("Goblin", "Thrower", False),
    "valkyrie": ("Clan", "Brutalist", False),  # Changed from Juggernaut to Brutalist
    "witch": ("Undead", "Superstar", False),  # Changed from Avenger to Superstar
    "wizard": ("Clan", "Blaster", False),  # Changed from Fire/Mage to Clan/Blaster
}

# List of all primary traits (7 total)
# Note: Electric, Fire, and some others are rotated out in Dec 2025
PRIMARY_TRAITS = [
    "Ace",
    "Clan",
    "Electric",  # Rotated out
    "Fire",      # Rotated out
    "Giant",     # New
    "Goblin",
    "Noble",
    "P.E.K.K.A", # New
    "Undead",
]

# List of all secondary traits (7 active in Dec 2025)
# Note: Avenger, Juggernaut, Mage are rotated out
SECONDARY_TRAITS = [
    "Assassin",
    "Avenger",    # Rotated out
    "Blaster",
    "Brawler",
    "Brutalist",  # New
    "Juggernaut", # Rotated out
    "Mage",       # Rotated out
    "Ranger",
    "Superstar",  # New
    "Thrower",
]

# Active traits in December 2025 season
ACTIVE_PRIMARY_TRAITS = ["Ace", "Clan", "Giant", "Goblin", "Noble", "P.E.K.K.A", "Undead"]
ACTIVE_SECONDARY_TRAITS = ["Assassin", "Blaster", "Brawler", "Brutalist", "Ranger", "Superstar", "Thrower"]

# List of all 29 troops (including rotated out, excluding skeleton spawned unit)
ALL_TROOP_TYPES = [
    "archer", "archer_queen", "baby_dragon", "bandit", "barbarian",
    "dart_goblin", "e_wiz", "electro_giant", "executioner", "giant_skeleton",
    "goblin", "goblin_machine", "golden_knight", "knight", "mega_knight",
    "mini_pekka", "monk", "musketeer", "pekka", "prince",
    "princess", "royal_ghost", "royal_giant", "skeleton_dragon",
    "skeleton_king", "spear_goblin", "valkyrie", "witch", "wizard"
]

# List of only active troops (24 troops, rotated out and skeleton excluded)
# Note: skeleton excluded as it's a spawned unit, not purchasable
ACTIVE_TROOP_TYPES = [
    "archer_queen", "bandit", "barbarian",
    "dart_goblin", "electro_giant", "executioner",
    "goblin", "goblin_machine", "golden_knight", "mega_knight",
    "mini_pekka", "monk", "musketeer", "pekka", "prince",
    "princess", "royal_ghost", "royal_giant", "skeleton_dragon",
    "skeleton_king", "spear_goblin", "valkyrie", "witch", "wizard"
]

# Rotated out troops (5 troops)
ROTATED_OUT_TROOPS = ["archer", "baby_dragon", "e_wiz", "giant_skeleton", "knight"]

# Correct elixir costs for ACTIVE troops (from mergetacticsbuild.com)
ACTIVE_TROOP_COSTS = {
    "archer_queen": 5,
    "bandit": 4,
    "barbarian": 2,
    "dart_goblin": 3,
    "electro_giant": 3,
    "executioner": 3,
    "goblin": 2,
    "goblin_machine": 4,
    "golden_knight": 5,
    "mega_knight": 4,
    "mini_pekka": 2,
    "monk": 5,
    "musketeer": 3,
    "pekka": 3,
    "prince": 3,
    "princess": 4,
    "royal_ghost": 4,
    "royal_giant": 2,
    # "skeleton": removed - spawned unit, not purchasable
    "skeleton_dragon": 2,
    "skeleton_king": 5,
    "spear_goblin": 2,
    "valkyrie": 3,
    "witch": 4,
    "wizard": 2,
}


def get_troop_traits(troop_name):
    """
    Get the primary and secondary traits for a troop.

    Args:
        troop_name: Name of the troop (e.g., "archer", "pekka")

    Returns:
        tuple: (primary_trait, secondary_trait, is_rotated_out)
    """
    return TROOP_TRAITS.get(troop_name, ("Unknown", "Unknown", False))


def get_troop_cost(troop_name):
    """
    Get the elixir cost for a troop.

    Args:
        troop_name: Name of the troop (e.g., "dart_goblin", "pekka")

    Returns:
        int: Elixir cost (2-5 for most troops, 0 for skeleton)
    """
    return ACTIVE_TROOP_COSTS.get(troop_name, 0)


def count_trait_activations(troop_counts):
    """
    Count how many UNIQUE TROOP TYPES have each trait.

    Example: If you have 5 bandits (Ace + Assassin) and 3 dart_goblins (Goblin + Ranger),
    the result is: Ace=1, Assassin=1, Goblin=1, Ranger=1 (not 5 and 3).

    Args:
        troop_counts: dict mapping troop_name -> count

    Returns:
        dict: {
            'primary': {trait_name: num_unique_troop_types, ...},
            'secondary': {trait_name: num_unique_troop_types, ...}
        }
    """
    primary_counts = {trait: 0 for trait in PRIMARY_TRAITS}
    secondary_counts = {trait: 0 for trait in SECONDARY_TRAITS}

    # Count unique troop types per trait (not total troops)
    for troop_name, count in troop_counts.items():
        if count > 0:
            primary, secondary, _ = get_troop_traits(troop_name)
            if primary in primary_counts:
                primary_counts[primary] += 1  # +1 per troop TYPE, not per troop count
            if secondary in secondary_counts:
                secondary_counts[secondary] += 1  # +1 per troop TYPE, not per troop count

    return {
        'primary': primary_counts,
        'secondary': secondary_counts
    }


def get_trait_state_features(troop_counts, only_active=True):
    """
    Convert troop counts to trait count features for RL state vector.

    Counts UNIQUE TROOP TYPES per trait (not total troops).
    Example: 5 bandits + 3 dart_goblins = Ace:1, Goblin:1, Assassin:1, Ranger:1

    Args:
        troop_counts: dict mapping troop_name -> count (0-27)
        only_active: bool, if True only include active traits (14 features),
                     if False include all traits (19 features)

    Returns:
        list: Normalized trait counts [primary_traits + secondary_traits]
              Each value normalized to [0, 1] by dividing by max trait count (5)

              If only_active=True: 14 features (7 primary + 7 secondary)
              If only_active=False: 19 features (9 primary + 10 secondary)
    """
    trait_counts = count_trait_activations(troop_counts)

    # Combine primary and secondary trait counts into a feature vector
    features = []

    # Choose which traits to include
    primary_list = ACTIVE_PRIMARY_TRAITS if only_active else PRIMARY_TRAITS
    secondary_list = ACTIVE_SECONDARY_TRAITS if only_active else SECONDARY_TRAITS

    # Max normalization value for trait counts
    MAX_TRAIT_COUNT = 5

    # Add primary trait counts (normalized)
    for trait in primary_list:
        count = trait_counts['primary'].get(trait, 0)
        normalized = min(count, MAX_TRAIT_COUNT) / MAX_TRAIT_COUNT
        features.append(normalized)

    # Add secondary trait counts (normalized)
    for trait in secondary_list:
        count = trait_counts['secondary'].get(trait, 0)
        normalized = min(count, MAX_TRAIT_COUNT) / MAX_TRAIT_COUNT
        features.append(normalized)

    return features


# Example usage
if __name__ == "__main__":
    # Example troop counts
    example_troops = {
        "archer": 2,
        "dart_goblin": 3,
        "golden_knight": 1,
        "pekka": 1,
    }

    print("Troop Traits:")
    for troop, count in example_troops.items():
        primary, secondary, rotated = get_troop_traits(troop)
        status = " (ROTATED OUT)" if rotated else ""
        print(f"  {troop}: {primary} + {secondary}{status}")

    print("\nTrait Activation Counts:")
    counts = count_trait_activations(example_troops)
    print("  Primary:", {k: v for k, v in counts['primary'].items() if v > 0})
    print("  Secondary:", {k: v for k, v in counts['secondary'].items() if v > 0})

    print("\nState Features (normalized - ACTIVE traits only):")
    features = get_trait_state_features(example_troops, only_active=True)
    print(f"  {len(features)} trait features (7 primary + 7 secondary):", features)

    print("\nState Features (normalized - ALL traits):")
    features_all = get_trait_state_features(example_troops, only_active=False)
    print(f"  {len(features_all)} trait features (9 primary + 10 secondary):", features_all)

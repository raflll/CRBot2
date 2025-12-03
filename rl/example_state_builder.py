"""
Example: Building RL State Vector with Trait Features

This shows how to construct the complete state vector including trait counts.
"""

import numpy as np
from troop_traits import (
    get_trait_state_features,
    TROOP_TRAITS,
    ACTIVE_TROOP_TYPES,
    ROTATED_OUT_TROOPS
)

# Constants
# Use only ACTIVE troops (25 troops, excludes rotated out)
TROOP_TYPES = ACTIVE_TROOP_TYPES

PRACTICAL_MAX_ELIXIR = 100


def build_state_vector(
    troop_counts,
    current_elixir,
    slot_1_troop,
    slot_2_troop,
    slot_3_troop
):
    """
    Build complete RL state vector with trait features.
    Only includes active troops (24 troops, excludes 5 rotated out + skeleton spawned unit).

    Args:
        troop_counts: dict mapping troop_name -> count (e.g., {"dart_goblin": 2, "pekka": 1})
        current_elixir: int, current elixir amount
        slot_1_troop: str, troop name in shop slot 1 (must be active troop)
        slot_2_troop: str, troop name in shop slot 2 (must be active troop)
        slot_3_troop: str, troop name in shop slot 3 (must be active troop)

    Returns:
        np.array: State vector of shape (111,)
            - [0:23]     Troop counts - 24 active troops (normalized)
            - [24]       Elixir (normalized)
            - [25:48]    Card slot 1 - 24 active troops (one-hot)
            - [49:72]    Card slot 2 - 24 active troops (one-hot)
            - [73:96]    Card slot 3 - 24 active troops (one-hot)
            - [97:103]   Primary trait counts - 7 active traits (normalized)
            - [104:110]  Secondary trait counts - 7 active traits (normalized)
    """
    state = []

    # 1. TROOP COUNTS (indices 0-23) - 24 features (active troops only, no skeleton)
    for troop in TROOP_TYPES:
        count = troop_counts.get(troop, 0)
        normalized_count = min(count, 27) / 27.0
        state.append(normalized_count)

    # 2. ELIXIR (index 24) - 1 feature
    normalized_elixir = min(current_elixir, PRACTICAL_MAX_ELIXIR) / PRACTICAL_MAX_ELIXIR
    state.append(normalized_elixir)

    # 3. CARD SLOT 1 (indices 25-48) - 24 features (one-hot, active troops only)
    slot_1_onehot = [0.0] * 24
    slot_1_index = TROOP_TYPES.index(slot_1_troop)
    slot_1_onehot[slot_1_index] = 1.0
    state.extend(slot_1_onehot)

    # 4. CARD SLOT 2 (indices 49-72) - 24 features (one-hot, active troops only)
    slot_2_onehot = [0.0] * 24
    slot_2_index = TROOP_TYPES.index(slot_2_troop)
    slot_2_onehot[slot_2_index] = 1.0
    state.extend(slot_2_onehot)

    # 5. CARD SLOT 3 (indices 73-96) - 24 features (one-hot, active troops only)
    slot_3_onehot = [0.0] * 24
    slot_3_index = TROOP_TYPES.index(slot_3_troop)
    slot_3_onehot[slot_3_index] = 1.0
    state.extend(slot_3_onehot)

    # 6. TRAIT FEATURES (indices 97-110) - 14 features (only active traits)
    trait_features = get_trait_state_features(troop_counts, only_active=True)
    state.extend(trait_features)

    return np.array(state, dtype=np.float32)


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("EXAMPLE: Building RL State Vector (111 features)")
    print("=" * 70)

    # Example game state
    example_troop_counts = {
        "dart_goblin": 3,
        "spear_goblin": 2,
        "golden_knight": 1,
        "pekka": 1,
        # ... all other troops default to 0
    }

    example_elixir = 35
    example_slot_1 = "dart_goblin"
    example_slot_2 = "golden_knight"
    example_slot_3 = "prince"

    print("\n1. GAME STATE")
    print("-" * 70)
    print(f"Troops on battlefield:")
    for troop, count in example_troop_counts.items():
        if count > 0:
            primary, secondary, _ = TROOP_TRAITS[troop]
            print(f"  - {troop}: {count} troops ({primary} + {secondary})")
    print(f"Current elixir: {example_elixir}")
    print(f"Shop slots: [{example_slot_1}, {example_slot_2}, {example_slot_3}]")

    # Build state vector
    state = build_state_vector(
        example_troop_counts,
        example_elixir,
        example_slot_1,
        example_slot_2,
        example_slot_3
    )

    print("\n2. STATE VECTOR BREAKDOWN")
    print("-" * 70)
    print(f"Total features: {len(state)}")
    print(f"\nIndices 0-23 (Troop counts - 24 active troops):")
    dart_idx = TROOP_TYPES.index("dart_goblin")
    spear_idx = TROOP_TYPES.index("spear_goblin")
    knight_idx = TROOP_TYPES.index("golden_knight")
    pekka_idx = TROOP_TYPES.index("pekka")
    print(f"  dart_goblin (index {dart_idx}): {state[dart_idx]:.3f} (= 3/27)")
    print(f"  spear_goblin (index {spear_idx}): {state[spear_idx]:.3f} (= 2/27)")
    print(f"  golden_knight (index {knight_idx}): {state[knight_idx]:.3f} (= 1/27)")
    print(f"  pekka (index {pekka_idx}): {state[pekka_idx]:.3f} (= 1/27)")

    print(f"\nIndex 24 (Elixir):")
    print(f"  {state[24]:.3f} (= 35/100)")

    print(f"\nIndices 25-48 (Slot 1 = dart_goblin):")
    slot_1_start = 25
    slot_1_active = np.where(state[slot_1_start:slot_1_start+24] == 1.0)[0][0]
    print(f"  One-hot index {slot_1_active}: {TROOP_TYPES[slot_1_active]}")

    print(f"\nIndices 97-110 (Trait features):")
    trait_features = state[97:]
    print(f"  Total trait features: {len(trait_features)}")
    print(f"  First 7 (primary traits): {trait_features[:7]}")
    print(f"  Last 7 (secondary traits): {trait_features[7:]}")

    # Show trait breakdown
    from troop_traits import count_trait_activations, ACTIVE_PRIMARY_TRAITS, ACTIVE_SECONDARY_TRAITS
    trait_counts = count_trait_activations(example_troop_counts)

    print(f"\n3. TRAIT ACTIVATION BREAKDOWN")
    print("-" * 70)
    print("Primary traits:")
    for i, trait in enumerate(ACTIVE_PRIMARY_TRAITS):
        count = trait_counts['primary'][trait]
        if count > 0:
            print(f"  {trait}: {count} troops (normalized: {trait_features[i]:.3f})")

    print("\nSecondary traits:")
    for i, trait in enumerate(ACTIVE_SECONDARY_TRAITS):
        count = trait_counts['secondary'][trait]
        if count > 0:
            print(f"  {trait}: {count} troops (normalized: {trait_features[7+i]:.3f})")

    print("\n4. USAGE")
    print("-" * 70)
    print("To use this in your DQN:")
    print("1. Import: from rl.example_state_builder import build_state_vector")
    print("2. Create DQN model: DQN(state_size=111, action_size=4)")
    print("3. Build state from CV data:")
    print("   state = build_state_vector(troop_counts, elixir, slot1, slot2, slot3)")
    print("4. Feed to network: q_values = model(state)")
    print("\nState includes:")
    print("  - 24 active troop counts (excludes 5 rotated out + skeleton spawned unit)")
    print("  - 1 elixir value")
    print("  - 72 card slot features (3 slots × 24 troops)")
    print("  - 14 trait features (auto-parsed from troop counts)")
    print(f"\nExcluded troops (NOT in state): {', '.join(ROTATED_OUT_TROOPS)} + skeleton (spawned)")
    print("=" * 70)

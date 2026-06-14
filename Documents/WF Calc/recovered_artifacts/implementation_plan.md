# Phase 9A: Melee Combo Foundation

The goal of this phase is to expand the evaluation engine to natively support Warframe's most crucial melee scaling vectors: Combo Multiplier and Combo Count. By integrating these systems, we can natively simulate the two most iconic melee scaling mods—Blood Rush and Weeping Wounds—using the exact same `ScalingEffect` architecture.

> [!NOTE]
> We are focusing strictly on the Combo Foundation (Phase 9A), avoiding full Stance simulation (Phase 9C) or heavy attack logic (Phase 9B) for now.

## Proposed Changes

### 1. Unified Combo State

#### [MODIFY] `src/lib/engine/types.ts`
Group combo properties into a dedicated `ComboState` within the overall `CombatState`.
```typescript
export type ComboState = {
  count: number;
  multiplier: number;
};

export interface CombatState {
  // ...
  combo?: ComboState; // Will be injected or estimated
}
```

### 2. Combo Estimation Logic

#### [NEW] `src/lib/engine/evaluator/comboEstimator.ts`
Implement `estimateComboState` analogous to `statusEstimator.ts`.
- `FRESH_TARGET`: `{ count: 0, multiplier: 1 }`
- `SUSTAINED_FIRE`: Estimated heuristic (e.g. 8x default for melee in V1, laying ground for checking attack speed/duration later).
- `MAX_STACKS`: `{ count: 220, multiplier: 12 }`

#### [MODIFY] `src/lib/engine/calculator/index.ts`
Inject `estimateComboState` into the early evaluation logic (Phase 1.5). Map the estimated `multiplier` to `stackCounts[ScalingSource.COMBO_MULTIPLIER]`.

### 3. Scaling Stat Logic Updates

#### [MODIFY] `src/lib/engine/evaluator/effects/ScalingStat.ts`
Update the engine to handle the unique `-1` math for combo multipliers.
```typescript
let currentStacks = 0;

if (sourceMetric === ScalingSource.COMBO_MULTIPLIER) {
  // 12x combo = 11 stacks. 1x combo = 0 stacks.
  const comboMult = context.combatState.combo?.multiplier || 1;
  currentStacks = Math.max(0, comboMult - 1);
} else {
  // Default stack fetching
}
```

### 4. Parser Support

#### [MODIFY] `src/lib/engine/parser/registry.ts`
Add parser patterns mapped purely to the generic `ScalingStat` engine:
- `Critical Chance stacks with Combo Multiplier` -> `ScalingSource.COMBO_MULTIPLIER`, `ModifierStat.CRIT_CHANCE`
- `Status Chance stacks with Combo Multiplier` -> `ScalingSource.COMBO_MULTIPLIER`, `ModifierStat.STATUS_CHANCE`

### 5. Verification Plan

#### [NEW] `test-combo-scaling.ts`
1. Assert that `Blood Rush` and `Weeping Wounds` correctly parse.
2. Assert specific unit test boundaries for the multiplier math:
   - 1x = 0 units
   - 2x = 1 unit
   - 5x = 4 units
   - 12x = 11 units
3. Assert that `CombatMode` defaults appropriately govern the combo multiplier.

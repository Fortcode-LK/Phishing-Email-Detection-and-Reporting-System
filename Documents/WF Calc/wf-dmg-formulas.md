# Warframe Damage Engine – Formulas and Explanations

This document summarizes a practical damage model for Warframe that you can implement in a TypeScript damage engine. It matches commonly used community formulas for base damage, elements, multishot, fire rate, and multi‑tier critical hits (yellow/orange/red), and includes simple burst and sustained DPS.[web:3][web:7][web:13]

All percentages are first converted to ratios (e.g., 165% → 1.65) before being used in formulas.[web:7]

---

## 1. Symbol definitions

Let the following base stats and aggregated modifiers be defined:

- \(BD\): Base damage from the weapon (sum of IPS plus any innate elemental damage from the database).[web:13]
- \(M_{BD}\): Sum of base damage mods as a ratio (e.g., two +165% damage mods → 1.65 + 1.65 = 3.30).[web:13]
- \(M_{elem}\): Sum of elemental damage mods as a ratio (e.g., four 90% elementals → 0.9 + 0.9 + 0.9 + 0.9 = 3.6).[web:7][web:13]
- \(M_{faction}\): Sum of faction (Bane) mods as a ratio.[web:7][web:13]
- \(MS_{base}\): Base multishot (usually 1.0 for rifles; higher for some shotguns).[web:7]
- \(M_{MS}\): Sum of multishot mods as a ratio (e.g., +90% + 60% → 1.5).[web:7]
- \(FR_{base}\): Base fire rate in shots per second.[web:3]
- \(M_{FR}\): Sum of fire‑rate mods as a ratio (e.g., +60% fire rate → 0.6).[web:13]
- \(CC_{base}\): Base critical chance as a fraction from 0 to 1 (e.g., 0.2 for 20%).[web:22]
- \(M_{CC}\): Sum of critical chance bonuses as a ratio (e.g., +150% crit chance → 1.5).[web:22]
- \(CM_{base}\): Base critical damage multiplier (e.g., 2.0).[web:21]
- \(M_{CM}\): Sum of critical damage bonuses as a ratio (e.g., +120% crit damage → 1.2).[web:23]
- \(Mag\): Magazine size.[web:3]
- \(Reload\): Reload time in seconds.[web:3]

All of the \(M_\*\) terms come from your aggregated mod dictionary (StatAggregator), where you have already summed all mods of the same type into a single value.

---

## 2. Modded damage and elemental damage

### 2.1 Modded base damage

Base damage mods are applied additively within their category, then multiplicatively on the base damage:[web:7][web:13]

\[
BD_{mod} = BD \times (1 + M_{BD})
\]

### 2.2 Elemental damage and pre‑faction hit damage

Elemental mods also add together, but they scale the **modded** base damage:[web:7][web:13]

\[
D_{elem} = BD_{mod} \times M_{elem}
\]

Total hit damage before faction multipliers is then:

\[
D_{hit,\,prefaction} = BD_{mod} + D_{elem} = BD \times (1 + M_{BD}) \times (1 + M_{elem})
\]

This is mathematically equivalent to the common Warframe community form \(BD \times (1 + MD) \times (1 + ED)\) where \(MD\) and \(ED\) are total base and elemental mod ratios.[web:7]

### 2.3 Faction (Bane) damage

Faction mods form a separate multiplicative stage and are applied after base and elemental damage:[web:7][web:13]

\[
D_{hit} = D_{hit,\,prefaction} \times (1 + M_{faction})
\]

For this engine, \(D_{hit}\) is the **non‑crit, non‑status** damage of a single projectile hitting an appropriate target.

> Note: In the live game, faction mods can also “double‑dip” with some damage‑over‑time procs (e.g., Slash). This simplified model does not include that effect.[web:3]

---

## 3. Final critical stats

Critical chance and critical multiplier are modified in a similar way: modifiers of the same type sum as ratios and then scale the base stat.

### 3.1 Final crit chance

\[
CC_{final} = CC_{base} \times (1 + M_{CC})
\]

Here \(CC_{final}\) is a fractional value that can exceed 1.0; for example \(CC_{final} = 1.85\) means 185% crit chance, which corresponds to guaranteed crits plus a chance to upgrade to higher crit tiers (orange/red).[web:18][web:22]

### 3.2 Final crit multiplier

\[
CM_{final} = CM_{base} \times (1 + M_{CM})
\]

This matches the way crit damage mods (e.g., Vital Sense, Organ Shatter) scale the base crit multiplier.[web:21][web:23]

---

## 4. Multi‑tier critical hits (yellow, orange, red)

Warframe supports multiple crit tiers:

- Tier 0: no crit.
- Tier 1: yellow crit.
- Tier 2: orange crit.
- Tier 3 and above: red crit tiers.[web:18][web:24][web:25]

For a given crit tier \(T\), the effective critical damage multiplier is:[web:16][web:18]

\[
CM_T = 1 + T \times (CM_{final} - 1)
\]

Some examples:

- Tier 1 (yellow): \(CM_1 = 1 + 1 \times (CM_{final} - 1) = CM_{final}\).
- Tier 2 (orange): \(CM_2 = 1 + 2 \times (CM_{final} - 1)\).
- Tier 3 (first red): \(CM_3 = 1 + 3 \times (CM_{final} - 1)\).[web:16][web:23]

### 4.1 Converting crit chance to tiers and probabilities

Given \(CC_{final}\):

1. Compute the integer **base tier**:

   \[
   T = \lfloor CC_{final} \rfloor
   \]

2. Compute the **fractional overflow**:

   \[
   f = CC_{final} - T
   \]

3. The interpretation is:
   - You always get at least a tier \(T\) crit.
   - With probability \(f\), that crit is upgraded by one tier to \(T + 1\).[web:18][web:25]

For example, \(CC_{final} = 2.4\) implies:

- \(T = 2\) (guaranteed orange crit).
- \(f = 0.4\) (40% chance to upgrade to red crit tier 3).[web:18]

### 4.2 Expected critical damage multiplier

Define the tier‑specific multiplier function:

\[
CM_T = 1 + T \times (CM_{final} - 1)
\]

Then the **expected** critical multiplier is:

- For \(0 \le CC_{final} < 1\) (no overflow, only non‑crit and tier‑1 crit):

  \[
  E[CM] = (1 - CC_{final}) \times CM_0 + CC_{final} \times CM_1 = 1 + CC_{final} \times (CM_{final} - 1)
  \]

  This reduces to the classic linear crit formula used in simpler DPS calculators.[web:23]

- For \(CC_{final} \ge 1\):

  \[
  E[CM] = (1 - f) \times CM_T + f \times CM_{T+1}
  \]

This formula correctly handles orange and red crits in the expected damage.[web:16][web:18][web:23]

### 4.3 Engine‑friendly pseudocode

In TypeScript, using the aggregated crit stats:

```ts
const CC_final  = CC_base * (1 + M_CC);
const CM_final  = CM_base * (1 + M_CM);

const critTier  = Math.floor(CC_final);      // 0, 1, 2, 3, ...
const frac      = CC_final - critTier;       // 0 <= frac < 1

const cmTier = (tier: number) => 1 + tier * (CM_final - 1);

const expectedCM = (1 - frac) * cmTier(critTier) + frac * cmTier(critTier + 1);
```

This `expectedCM` is the factor you multiply the non‑crit hit damage with to get the average damage per projectile, including all crit tiers.[web:16][web:18][web:23]

---

## 5. Average damage per projectile (with crits)

Once you have the non‑crit hit damage \(D_{hit}\) and the expected crit multiplier \(E[CM]\):

\[
D_{proj,\,avg} = D_{hit} \times E[CM]
\]

This gives the average damage of a single projectile against an appropriate target, accounting for the full crit tier behavior but ignoring status and armor.[web:2][web:3]

For the special case \(CC_{final} \le 1\), this reduces to the common form:

\[
D_{proj,\,avg} = D_{hit} \times \bigl(1 + CC_{final} \times (CM_{final} - 1)\bigr)
\]

which many simple calculators use as an approximation.[web:20][web:23]

---

## 6. Multishot, fire rate, and burst DPS

### 6.1 Final multishot and fire rate

Multishot and fire‑rate modifiers are also additive within their category and then multiplicative on the base stat:[web:7][web:13]

\[
MS_{final} = MS_{base} \times (1 + M_{MS})
\]

\[
FR_{final} = FR_{base} \times (1 + M_{FR})
\]

For DPS purposes, \(MS_{final}\) can be interpreted as the **expected number of projectiles per trigger pull**.[web:2][web:3]

### 6.2 Burst DPS (no reload considered)

Burst DPS assumes infinite magazine and no reload downtime. It is simply:

\[
DPS_{burst} = D_{proj,\,avg} \times FR_{final} \times MS_{final}
\]

This is “average damage per projectile” multiplied by “projectiles per second”.[web:2][web:3][web:20]

> Note: In the real game, multishot affects both damage and status/crit rolls per projectile, which matters especially for shotguns and status builds. This simplified engine treats multishot as a scalar expected projectile count and does not model per‑pellet status distribution.[web:3][web:12]

---

## 7. Sustained DPS (with magazine and reload)

To approximate sustained DPS over a long fight, include magazine size and reload time.

### 7.1 Time to empty the magazine

Use the **shot** fire rate (not multiplied by multishot) to compute how long it takes to fire the whole magazine:[web:3]

\[
T_{empty} = \frac{Mag}{FR_{final}}
\]

### 7.2 Firing uptime fraction

Sustained firing consists of firing the magazine and then reloading repeatedly. The fraction of time spent firing (as opposed to reloading) is:

\[
U_{fire} = \frac{T_{empty}}{T_{empty} + Reload}
\]

### 7.3 Sustained DPS

Finally, sustained DPS is burst DPS scaled by the firing uptime:[web:3][web:20]

\[
DPS_{sustained} = DPS_{burst} \times U_{fire}
\]

This matches the simple “magazine plus reload” sustained DPS model used in many community calculators.[web:3][web:20]

---

## 8. How to wire this into your Next.js engine

Inside your `DamageCalculator.ts` you can follow this pipeline:

1. **Input**: `WeaponBaseStats`, `AggregatedModifiers` from your SQLite DB and `StatAggregator`.
2. **Compute modded damage**:
   - Compute \(BD_{mod}\) from \(BD\) and \(M_{BD}\).
   - Compute \(D_{elem}\) from \(BD_{mod}\) and \(M_{elem}\).
   - Compute \(D_{hit}\) via faction multiplier.
3. **Compute crit stats**:
   - Compute \(CC_{final}\) and \(CM_{final}\).
   - Compute \(E[CM]\) using the tier‑based method.
4. **Compute projectile and DPS values**:
   - Compute \(D_{proj,\,avg}\).
   - Compute \(MS_{final}\) and \(FR_{final}\).
   - Compute \(DPS_{burst}\).
   - Compute \(DPS_{sustained}\) using \(Mag\), \(Reload\), and \(FR_{final}\).

With this structure, the engine remains clean and deterministic: each stage is a pure function of the previous one, and all mod stacking rules are captured in a consistent, Warframe‑accurate way for hitscan DPS without status or armor.[web:3][web:7][web:13]

# Specialized Weapons Database Creation Plan

This plan outlines how we will extract the remaining weapon datasets into two separate SQLite databases, as requested:
1. `arch_weapons.db` for Arch-Guns and Arch-Melee
2. `companion_weapons.db` for Sentinel and Hound weapons.

## User Review Required

> [!NOTE]
> I checked the downloaded `SentinelWeapons.json` data, and I can confirm that **Hound weapons** (like the *Akaten*, *Batoten*, and *Lacerten*) are already included inside this single JSON file alongside Sentinel weapons. 
> 
> Therefore, parsing `SentinelWeapons.json` will automatically cover both Sentinel and Hound weapons in `companion_weapons.db`.
>
> We will reuse the exact same unified schema we used for the main weapons database so your calculator logic can remain consistent across all databases. Does this approach look good to you?

## Proposed Changes

We will modify our database builder script or create two new scripts (`build_arch_db.py` and `build_companion_db.py`) to construct the databases.

### `arch_weapons.db`
- **Source Files:** `Arch-Gun.json`, `Arch-Melee.json`
- **Schema:** Unified `weapons` table (same as `weapons.db`)
- **Use Case:** Tracking heavy weapons used in space, underwater, and as heavy weapons in terrestrial missions.

### `companion_weapons.db`
- **Source Files:** `SentinelWeapons.json`
- **Schema:** Unified `weapons` table (same as `weapons.db`)
- **Use Case:** Tracking robotic companion armaments (Sentinels, Hounds, MOAs).

## Verification Plan

### Automated Tests
- Create verification scripts to ensure the new databases are populated correctly.
- For `arch_weapons.db`, query a sample Arch-Gun (e.g., *Imperator Vandal*) and Arch-Melee (e.g., *Centaur*).
- For `companion_weapons.db`, query a sample Sentinel weapon (e.g., *Sweeper Prime*) and a Hound weapon (e.g., *Lacerten*).

### Manual Verification
- The user can inspect the resulting SQLite databases.
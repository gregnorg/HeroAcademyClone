# Fidelity ledger

Target: original Hero Academy, Council and Dark Elves. This is an independent reconstruction, not verified original code. Numerical parity is a goal, not a completed claim. The launch-era stat baseline is deliberately separate from later balance values.

## Sources

- [Maurice Tan's firsthand launch guide, Jan 13 2012](https://www.destructoid.com/a-starters-guide-to-robot-entertainments-hero-academy/): Council base stats, melee modifiers, chain falloff, equipment, tile bonuses.
- [Wyatt Cheng's firsthand inventory count, Feb 4 2012](https://wyattcheng.blogspot.com/2012/02/): Council reserve composition (28 cards).
- [Niels Justesen's 2015 thesis, chapter 2](https://njustesen.github.io/njustesen/publications/justesen-masterthesis.pdf): map coordinates, movement, healing, potion revive.
- [Hamlet's guide announcement](https://www.robotentertainmentfans.com/2012/08/16/detailed-hero-academy-mechanics-guide/): additional reference to recover; the linked mechanics page was unavailable during initial research.

## Council base numbers

| Unit | HP | Power | Move | Range | Physical resistance | Magic resistance |
|---|---:|---:|---:|---:|---:|---:|
| Knight | 1200 | 200 | 2 | 1 | 20% | 0% |
| Archer | 800 | 300 | 2 | 3 | 0% | 0% |
| Wizard | 800 | 200 | 2 | 2 | 0% | 0% |
| Cleric | 800 | 200 | 2 | 2 | 0% | 0% |
| Ninja | 800 | 200 | 3 | 2 | 0% | 0% |

The thesis differs on Knight health (1000), Ninja speed (5), Cleric resistance (20%), and Dragonscale health. We use the launch guide's baseline rather than silently mixing those stats. The thesis also describes 34 cards while its listed inventory totals 28, and labels the helm as physical resistance; those are not copied.

## Implemented with source support

Five actions; six-card hand; Manhattan movement; deployment; typed damage; Archer melee penalty; Ninja melee bonus and swap; Knight displacement; Wizard 100/75/50% chain damage; equipment; potions; Inferno; tile bonuses; knockouts, revives, stomps; crystal and army victory; turn reset. Each normal action costs one point.

## Provisional: do not label these exact

- Cross-version Cleric healing 600/revive 400 and potion revive 100 use thesis values pending a launch-client comparison.
- Map crystal health currently 4500 each; map layout follows the thesis illustration, not a verified launch map export.
- Wizard chain tie-break is nearest orthogonal neighbor, then row/column; original direction priority needs verification.
- Line of sight uses enemy-blocked center rays; corner intersections need original-client fixtures.
- Equipment health gain, rounding/order, scroll healing, splash assault bonus and corpse expiration require original-client checks.
- Card exchanges return to the bottom after refill. Original reshuffle behavior, opening-hand guarantees and starting-player selection need verification. Host starts in this build.
- Practice mode has predeployed pieces; it is explicitly not an authentic opening.

## Remaining product scope

Dwarves, Tribe, Shaolin, Team Fortress and additional maps, authenticated accounts, matchmaking, push notifications, production hosting, and original sound/animation parity remain separate milestones. Never replace an unknown mechanic with a claimed verified value.


## Dark Elves — first playable reconstruction

Base hero statistics, faction life leech, corpse abilities and item purposes follow the firsthand launch guide above. The deck follows the [firsthand inventory count](https://wyattcheng.blogspot.com/2012/02/): three each of the four standard heroes, one Wraith, three each sword/Soulstone/helm, and two each scroll/Mana Vial/Soul Harvest. Phantoms are summoned, never drawn.

These mechanics are **provisional**, not verified exact values:

- Life leech uses one third of actual health removed, or two thirds with Soulstone, rounded down; overkill, crystal and splash treatment need original-client comparison.
- Priestess heals at 2× power and revives at 0.5× power. Weakening halves the next attack only. The latter is corroborated by [Wyatt Cheng's firsthand January notes](https://wyattcheng.blogspot.com/2012/01/).
- Wraith consumption is an adjacent action with +150 HP/+50 power for its first three corpses. Corpse deployment grants the first growth stack. Growth/equipment ordering and whether deployment grants growth need comparison.
- Void Monk splash covers the target's two perpendicular neighbors and the square directly behind. Impaler diagonal pulls step diagonally; blocked pulls do not displace. These geometric choices need fixtures.
- Necromancer raising uses Manhattan range three; no line-of-sight check. Phantoms disappear at zero health and cannot use equipment or potions. Phantom leech and corpse behavior need comparison.
- Soul Harvest distributes actual damage / (3 + friendly hero count), rounded to nearest five, as both current and maximum health. No damage means no revival. The launch author explicitly could not establish its formula. This implementation is a provisional reconstruction, not a verified formula.
- Mana Vial adds a flat 50 maximum HP and heals 1000 without revival. Percentage equipment bonuses apply only to base HP; growth and harvested health are additive.

Old saved Council matches default to Council when faction metadata is absent. Existing hands, boards and decks are preserved. No original game art or source code is imported.

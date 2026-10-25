# Fidelity ledger

Target: original Hero Academy, starting with the Council. This is an independent reconstruction, not verified original code. Numerical parity is a goal, not a completed claim. The launch-era stat baseline is deliberately separate from later balance values.

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

Other factions and maps, authenticated accounts, matchmaking, push notifications, production hosting, and original sound/animation parity remain separate milestones. Never replace an unknown mechanic with a claimed verified value.

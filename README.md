# Crystal Tactics

A playable browser reconstruction of the original Hero Academy's Council, Dark Elf and Dwarf factions, with original illustrated characters. Runs locally in Docker with PostgreSQL match storage.

## Play

Open [the academy](http://localhost:8080) after starting Docker. Create an account with a username, email, and password (12–128 characters). Sign in with either username or email. Choose your faction and your opponent’s faction, then a mode:

- **Practice:** a deployed squad from each selected faction against a computer opponent that plans multi-action turns.
- **Pass & play:** two players on this Mac, with a handoff between turns.
- **Friendly duel:** one-time invitations between signed-in accounts for asynchronous play. The current localhost setup works only on this Mac; remote friends need hosting.

Plan up to five actions, undo or reset freely, then submit. Click any step in the action plan to undo that step and everything after it. Your draft survives browser reloads; committed turns live in PostgreSQL. The battle journal offers step-by-step replays for newly submitted turns, with a shortcut to the opponent’s last turn. Hover or focus an attack target to preview damage.

The game includes deployment, movement, equipment, combat, Wizard chains, Knight knockback, Ninja swaps, healing, revival, stomping, consumables, premium squares, reinforcements, victory, and resignation.

**Fidelity:** Council, Dark Elves and Dwarves are playable; the other three factions are not yet implemented. Launch-era stats are sourced, but several interactions and map values remain provisional. See [the fidelity ledger](docs/FIDELITY.md) for evidence, conflicting versions, and remaining work. This is not yet an exact or complete clone.

## Start on your Mac

Install and open Docker Desktop, then:

```sh
cd ~/Projects/HeroAcademyClone
# Generate the password only if .env does not already exist.
(umask 077; test -e .env || { printf 'POSTGRES_PASSWORD='; openssl rand -hex 32; } > .env)
docker compose up --build -d
```

Open http://localhost:8080. No registry account is required. Docker builds the app image from the Dockerfile and downloads the official PostgreSQL image.

## Everyday commands

```sh
docker compose ps
docker compose logs -f app
docker compose down          # keeps database volume
docker compose up -d
# After source changes:
docker compose up --build -d
```

Do not add `--volumes` to `down` unless you intend to erase matches. Changing `.env` does not update a password in an already initialized database volume.

## Architecture and saved data

Browser → localhost:8080 → Flask/Gunicorn app → PostgreSQL → named volume.

The app validates every action and locks a match during submission. Revision checks prevent duplicate or stale turns. Accounts own match sides; passwords are salted PBKDF2-SHA256 hashes. Seven-day sessions use revocable HttpOnly, SameSite cookies, with CSRF checks and login rate limits. Set `COOKIE_SECURE=1` when serving over HTTPS. Email addresses are unique and private; email verification and password recovery are not implemented yet.

Legacy player keys and their database columns have been removed. Old key-only matches remain stored but are inaccessible; there is no key-based claiming or guest play. New matches are listed from the signed-in account. Pass & play assigns both sides to that account. Drafts remain in browser storage.

Compose creates a private network between the two containers. Only the app port is published, bound to this Mac's loopback address. PostgreSQL files live in the `crystal-tactics_match-data` Docker volume. `.env` is excluded from Git and the image. This configuration is for local use; public deployment still needs HTTPS, backups, and operational hardening.

## Verification

Rules tests need only Python 3:

```sh
python3 -m unittest discover -s tests -p test_rules.py -v
python3 -m unittest discover -s tests -p test_bot.py -v
python3 -m unittest discover -s tests -p test_dark_elves.py -v
python3 -m unittest discover -s tests -p test_dwarves.py -v
```

API integration tests require the running Compose stack:

```sh
docker compose exec -T app python - < tests/test_api.py
docker compose exec -T app python - < tests/test_accounts.py
```

API tests create disposable matches and remove only their own rows. They exercise private access, invitations, preview/commit behavior, stale revisions, malformed actions, replay privacy, resignation, and bot responses. Browser checks cover turn planning, action-plan rewind, draft restoration, submission, replay controls, and pass-and-play handoff. The current planner completed seeded practice games 7 and 17 in 54 and 44 turns, respectively, with no occupancy or health invariant failures; the slowest turn took about 0.6 seconds on the development Mac. Seed 7 previously repeated a healing/attacking cycle under the greedy bot. This bounded planner is still beatable and does not guarantee optimal play.

## Source layout

- `rules.py`: deterministic faction game engine and public state filtering.
- `bot.py`: bounded turn planner for practice.
- `server.py`: authenticated match API and persistence.
- `public/`: browser interface, original SVG art, animation, and sound.
- `tests/`: rules and database integration checks.
- `docs/FIDELITY.md`: sourced values and explicit uncertainties.


Dark Elves add Void Monks, Impalers, Necromancers, Priestesses, Wraiths, summoned Phantoms, Soulstones, Mana Vials and Soul Harvest. Their card inventory is separate from Council. Faction selection is saved with each match and retained by Play again. Existing Council games continue unchanged. Dark Elf rounding, splash geometry, growth ordering and Soul Harvest distribution remain provisional; consult the fidelity ledger before treating those values as exact.


Dwarves use the February 2012 launch baseline: Paladin support healing, Gunner spread, Grenadier lobbed splash, Engineer shields, Annihilator knockback/armor weakening, premium-square bonuses, Dwarven Brew and Pulverizer. Later balance buffs are deliberately not mixed in. Shield lifetime, blocked displacement and consumable protection have regression tests.

All heroes use original rounded vector illustrations with expressive faces, faction equipment and subtle idle/blink motion. Attacks have wind-up/recoil, hit reactions and particles; shields and Brew have visible protection effects. Reduced-motion preferences disable these animations. These are original approximations, not the original sprites or animation files.

# Crystal Tactics

A playable browser reconstruction of the original Hero Academy's Council faction, with original illustrated characters. Runs locally in Docker with PostgreSQL match storage.

## Play

Open [the academy](http://localhost:8080) after starting Docker. Choose:

- **Practice:** a deployed Council squad against a simple computer opponent.
- **Pass & play:** two players on this Mac, with a handoff between turns.
- **Friendly duel:** private invitation and player links for asynchronous play. The current localhost setup works only on this Mac; remote friends need hosting.

Plan up to five actions, undo or reset freely, then submit. Your draft survives browser reloads; committed turns live in PostgreSQL. The battle journal offers step-by-step replays for newly submitted turns. Hover or focus an attack target to preview damage.

The game includes deployment, movement, equipment, combat, Wizard chains, Knight knockback, Ninja swaps, healing, revival, stomping, consumables, premium squares, reinforcements, victory, and resignation.

**Fidelity:** only Council is implemented. Launch-era stats are sourced, but several interactions and map values remain provisional. See [the fidelity ledger](docs/FIDELITY.md) for evidence, conflicting versions, and remaining work. This is not yet an exact or complete clone.

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

The app validates every action and locks a match during submission. Revision checks prevent duplicate or stale turns. Player links grant access to one side; only token hashes are stored in the database. The browser stores player links and unsubmitted drafts locally. Keep your private player link if you want to resume after clearing browser storage. There are no accounts or password recovery yet.

Compose creates a private network between the two containers. Only the app port is published, bound to this Mac's loopback address. PostgreSQL files live in the `crystal-tactics_match-data` Docker volume. `.env` is excluded from Git and the image. This configuration is for local use; public deployment still needs HTTPS, backups, and operational hardening.

## Verification

Rules tests need only Python 3:

```sh
python3 -m unittest discover -s tests -p test_rules.py -v
```

API integration tests require the running Compose stack:

```sh
docker compose exec -T app python - < tests/test_api.py
```

API tests create disposable matches and remove only their own rows. They exercise private access, invitations, preview/commit behavior, stale revisions, malformed actions, replay privacy, resignation, and bot responses. Browser checks cover turn planning, undo, draft restoration, submission, and replay controls.

## Source layout

- `rules.py`: deterministic Council game engine and public state filtering.
- `bot.py`: practice opponent.
- `server.py`: authenticated match API and persistence.
- `public/`: browser interface, original SVG art, animation, and sound.
- `tests/`: rules and database integration checks.
- `docs/FIDELITY.md`: sourced values and explicit uncertainties.

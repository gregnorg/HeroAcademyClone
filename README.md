# Crystal Tactics

Local Docker foundation for an asynchronous tactics game inspired by Hero Academy. Working title and visuals are original. This milestone includes a responsive board preview and a real PostgreSQL connectivity endpoint; gameplay and accounts are not implemented yet.

## First run on your Mac

1. Install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/) and open it. Wait until the Docker engine is running.
2. Open Terminal in this project folder:

   ```sh
   cd /Users/gregnorg/Projects/HeroAcademyClone
   ```

3. Generate a local database password once (leave an existing `.env` intact):

   ```sh
   (umask 077; test -e .env || { printf 'POSTGRES_PASSWORD='; openssl rand -hex 32; } > .env)
   ```

4. Build and start:

   ```sh
   docker compose up --build -d
   ```

5. Open http://localhost:8080. The status should read “App online · Database connected”.

## Everyday commands

```sh
docker compose ps             # container status
docker compose logs -f app    # app logs (Ctrl-C exits log viewing)
docker compose down           # remove containers; retain database volume
docker compose up -d          # start again
```

After source changes, use `docker compose up --build -d` to rebuild the app. Do not add `--volumes` to `down` unless you intend to erase the database. Changing `.env` does not change the password in an already-initialized PostgreSQL volume.

## How it fits together

Browser → localhost:8080 → app → db:5432 → match-data volume.

- App image: built from our Dockerfile; Python, Flask, Gunicorn, and the static website.
- Database image: official PostgreSQL 17 Alpine image, downloaded from Docker Hub.
- Compose supplies a private network and waits for PostgreSQL to become healthy.
- Only the app port is published, bound to the Mac's loopback address. Phone access is not enabled yet.
- Database files live in a Docker-managed named volume, not the image or this source folder. `.env` is excluded from Git and the app image.
- No registry account or cloud hosting is required for this local setup.

## Next milestones

1. Implement and test deterministic movement, combat, five-action turns, and undo.
2. Add a match schema, server-validated submissions, and saved turn history.
3. Add player identity and friend invitations for asynchronous play.
4. Deploy with HTTPS, production secrets, and database backups. This Compose file is for local development, not public deployment.

## Verification status

Source checks can run independently of Docker. Full container build, database connectivity, and browser checks require Docker Desktop to be installed and running; consult the delivery message for the checks actually completed.

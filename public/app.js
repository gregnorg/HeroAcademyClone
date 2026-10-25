const pieces = new Map([
  [19, ['◆', 'azure']], [25, ['◆', 'ember']],
  [11, ['♜', 'azure']], [29, ['✦', 'azure']],
  [15, ['✦', 'ember']], [33, ['♜', 'ember']],
]);
const board = document.querySelector('#board');
for (let index = 0; index < 45; index++) {
  const tile = document.createElement('div');
  tile.className = 'tile ' + ((Math.floor(index / 9) + index % 9) % 2 ? 'alternate' : '');
  const piece = pieces.get(index);
  if (piece) {
    tile.textContent = piece[0];
    tile.classList.add(piece[1]);
  } else if ([13, 31].includes(index)) {
    tile.textContent = '✚';
    tile.classList.add('healing');
  }
  board.append(tile);
}
async function checkConnection() {
  const status = document.querySelector('#status');
  const button = document.querySelector('#retry');
  button.disabled = true;
  status.textContent = 'Checking app and database…';
  try {
    const response = await fetch('/api/health', {signal: AbortSignal.timeout(6000)});
    const result = await response.json();
    status.textContent = response.ok && result.database === 'connected'
      ? '● App online · Database connected'
      : 'App online · Database unavailable';
  } catch {
    status.textContent = 'Connection unavailable. Start the app with Docker Compose.';
  } finally {
    button.disabled = false;
  }
}
document.querySelector('#retry').addEventListener('click', checkConnection);
checkConnection();

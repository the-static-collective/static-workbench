# Tonight local board

Open `SESSION_BOARD.html` directly in your browser after extracting the ZIP. No server, account, API key or network connection is required to use the board. The underlying original Story Desk remains separately available using `npm start` from the parent directory.

The board does NOT auto-save, post to an API, read the local Story Desk, sign for anyone, create a world or authenticate a person. It holds form data in this tab only until the page is closed, refreshed or cleared. Use the deliberate private Markdown/JSON export. The browser may save exports in a cloud-synced Downloads directory; choose your own safe file location. To resume, import a JSON backup manually. It is not a replacement for the original creative app or its privacy architecture.

To check the static interface: `node --check` cannot parse HTML directly; use a browser and inspect that the action buttons work, downloads contain private fields, import restores values, and refreshing discards unsaved input. No vendor integrations are implied by this file.

import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

// Integration-only verifier: imports the PINNED reLATTE owner implementation.
// The browser runtime and Python bridge do not implement a shadow verifier.
const root = process.env.RELATTE_ROOT;
if (!root) throw new Error('RELATTE_ROOT is required');
const { verifyCrossingEnvelope, verifyReceipt } =
  await import(pathToFileURL(resolve(root, 'src/protocol.ts')).href);
const chunks = [];
for await (const chunk of process.stdin) chunks.push(chunk);
const packet = JSON.parse(Buffer.concat(chunks).toString('utf8'));
const crossing = packet.crossing;
const received = packet.receive_receipt;
const disposition = packet.disposition_receipt;
const answer = {
  crossing_verified: await verifyCrossingEnvelope(crossing),
  receive_verified: await verifyReceipt(received),
  disposition_verified: await verifyReceipt(disposition),
};
process.stdout.write(JSON.stringify(answer) + '\n');

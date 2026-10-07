"use strict";
// WEBZ-NATIVE-001: noncanonical browser-local navigation testimony.
// No human identity, notes, material carry, signatures, or admission semantics.
const SCHEMA = "webz/voyage-local/v0";
const PROJECTION = "webz/voyage-projection/v0";
const LAW = "browser-local-observation";
const A = "webz:the-static-collective/sanctuary";
const B = "webz:the-static-collective/orchard-022100";
const DOORS = new Map([
  [`${A}|${B}`, "sanctuary-to-orchard"],
  [`${B}|${A}`, "orchard-to-sanctuary"],
]);
const BASE = ["seq","kind","from_world_id","to_world_id","door_id","carry_mode","authority"];
const own = (value) => value && typeof value === "object" && !Array.isArray(value);
const exact = (value, keys) => own(value) &&
  Object.keys(value).length === keys.length && keys.every((key) => Object.hasOwn(value,key));

function validWorld(world_id) {
  if (world_id !== A && world_id !== B) throw new Error("unknown local world identity");
}
function validateEvent(event, seq) {
  const keys = event?.kind === "arrived" ? [...BASE,"basis_departure_seq"] : BASE;
  if (!exact(event, keys)) throw new Error("unexpected local voyage event fields");
  if (event.kind !== "departed" && event.kind !== "arrived") throw new Error("invalid event kind");
  if (!Number.isSafeInteger(event.seq) || event.seq !== seq) throw new Error("invalid event sequence");
  validWorld(event.from_world_id);
  validWorld(event.to_world_id);
  if (DOORS.get(`${event.from_world_id}|${event.to_world_id}`) !== event.door_id) {
    throw new Error("undeclared world crossing or door");
  }
  if (event.carry_mode !== "none" || event.authority !== LAW) {
    throw new Error("unapproved carry or authority");
  }
  if (event.kind === "arrived" && (!Number.isSafeInteger(event.basis_departure_seq)
       || event.basis_departure_seq < 1)) throw new Error("invalid departure reference");
}

export function projectVoyage(events, initial_world_id) {
  validWorld(initial_world_id);
  if (!Array.isArray(events) || events.length > 512) throw new Error("invalid local voyage event sequence");
  const visits = [initial_world_id];
  let pending = null;
  let current = initial_world_id;
  for (let index=0; index<events.length; index++) {
    const event=events[index];
    validateEvent(event,index+1);
    if (event.kind === "departed") {
      if (pending || event.from_world_id !== current) throw new Error("departure is stale or duplicated");
      pending = event;
    } else {
      if (!pending || event.basis_departure_seq !== pending.seq ||
          event.from_world_id !== pending.from_world_id ||
          event.to_world_id !== pending.to_world_id ||
          event.door_id !== pending.door_id) throw new Error("unmatched or contradictory arrival");
      current = event.to_world_id;
      visits.push(current);
      pending = null;
    }
  }
  return {
    schema: PROJECTION,
    visits,
    pending_departure_seq: pending?.seq ?? null,
    current_world_id: current,
  };
}

export function appendVoyageEvent(events, event) {
  if (!Array.isArray(events) || !own(event)) throw new Error("invalid proposed event");
  const candidate = structuredClone(events);
  candidate.push(structuredClone(event));
  const first = candidate[0];
  projectVoyage(candidate,first.from_world_id);
  return candidate;
}

export function canonicalVoyageProjection(events, initial_world_id) {
  return JSON.stringify(projectVoyage(events, initial_world_id));
}

export function serializeVoyageExport(initial_world_id, events) {
  projectVoyage(events,initial_world_id);
  return JSON.stringify({schema:SCHEMA,initial_world_id,events:structuredClone(events)});
}

export function parseVoyageExport(text) {
  if (typeof text !== "string" || text.length > 65536) throw new Error("invalid export body");
  let data;
  try { data=JSON.parse(text); }
  catch (_) { throw new Error("corrupt local voyage export"); }
  if (!exact(data,["schema","initial_world_id","events"]) || data.schema !== SCHEMA) {
    throw new Error("unknown local voyage schema");
  }
  projectVoyage(data.events,data.initial_world_id);
  return {initial_world_id:data.initial_world_id,events:structuredClone(data.events)};
}

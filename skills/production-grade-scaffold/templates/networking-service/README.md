# Networking / Systems Service Skeleton

Read references/architecture-archetypes.md section 4 before using this - this archetype does
NOT fit the REST/DB layered model, and this skeleton is deliberately thinner than the other
templates because the right shape varies far more by protocol (raw TCP, UDP, custom binary,
MQTT, a proxy, etc.) than it does for REST services.

## Suggested module boundaries (adapt names to your protocol/language)

- protocol/    Wire format: framing, (de)serialization, message types. Fuzz-test this hardest -
               it's the most common source of parser/buffer-overrun bugs in this archetype.
- transport/   Connection lifecycle: accept/dial, handshake (incl. mTLS if used), keepalive,
               backpressure, graceful shutdown draining in-flight connections.
- session/     Per-connection state machine, if the protocol is stateful. This replaces the
               "domain layer" for many networking services - there may be no persistent
               database at all, or only an audit/metrics sink.
- domain/      Only include this if there's real business state beyond the connection itself
               (e.g. a policy engine, billing counters). If so, the Entities/Aggregates
               conventions from references/domain-structure.md still apply here.

## Security checklist specific to this archetype (see references/architecture-archetypes.md #4)
- mTLS or a protocol-level auth handshake in place of OAuth2/JWT bearer tokens.
- Connection-level rate limiting / max-connections-per-source instead of HTTP-request rate limits.
- Strict length-prefixed / bounded-size framing on every inbound message - never trust a
  length field without a hard upper bound before allocating a buffer for it.
- Fuzz testing (e.g. cargo-fuzz, AFL, go-fuzz) wired into CI against the protocol/ parser -
  this is the single highest-leverage addition for this archetype specifically.

## CI additions beyond the standard pipeline
Add a fuzz-testing stage (short, time-boxed run in CI; longer scheduled runs separately) targeting
the protocol parser, on top of the standard lint -> test -> SAST -> build+sign pipeline from
references/infrastructure-delivery.md.

## What this skeleton deliberately omits
No Dockerfile/docker-compose/DB config is assumed - add a database only if the service actually
needs persistent state beyond the connection/session layer. No REST route conventions apply.

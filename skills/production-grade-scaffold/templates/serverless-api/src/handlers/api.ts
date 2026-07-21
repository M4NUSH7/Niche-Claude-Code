import type { APIGatewayProxyHandlerV2 } from "aws-lambda";

// Initialize expensive clients OUTSIDE the handler body so they survive container reuse
// across warm invocations — see references/architecture-archetypes.md #3 (cold start).
// const db = createDbClient(); // lazy singleton, not a connection pool

export const handler: APIGatewayProxyHandlerV2 = async (event) => {
  // Auth: validate JWT signature/exp/aud here (see references/auth.md) before dispatching
  // to a route. Mount versioned routes by inspecting event.rawPath, or use a router lib.

  if (event.rawPath === "/healthz") {
    return { statusCode: 200, body: JSON.stringify({ status: "ok" }) };
  }

  return { statusCode: 404, body: JSON.stringify({ error: "not found" }) };
};

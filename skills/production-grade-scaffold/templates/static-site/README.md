# Static Site Production Scaffold

Generated from the `production-grade-scaffold` skill. Read references/cloud-providers.md's
"Plain website" section first - this archetype has no API/Domain/Data-Access layers at all.
If you later add forms/auth/dynamic data, that's a new archetype decision
(references/architecture-archetypes.md), usually CDN-attached functions rather than a full server.

- src/           - pages/content (swap the placeholder index.html for Astro/Hugo/Eleventy/plain HTML)
- _headers       - CDN-layer security headers (works on Cloudflare Pages/Netlify as-is)

Before first deploy, walk the shrunk security checklist in references/cloud-providers.md's
static-site section - most of references/security.md and all of auth.md/database.md don't apply
unless you've added a backend.

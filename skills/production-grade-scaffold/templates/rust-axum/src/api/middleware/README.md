# Middleware / tower layers

Auth enforcement (validate JWT signature/exp/aud at the edge) and rate limiting
(Sliding Window Counter via Redis, see references/api-layer.md) belong here as tower Layers.

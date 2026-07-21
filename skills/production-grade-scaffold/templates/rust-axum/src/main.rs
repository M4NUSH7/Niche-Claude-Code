use axum::{routing::get, Router};
use tower_http::cors::{AllowOrigin, CorsLayer};
use std::env;

mod api;
mod domain;
mod data_access;
mod infrastructure;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().json().init();

    // See references/security.md: static CORS allowlist, never reflect Origin when credentials on.
    let allowed: Vec<_> = env::var("ALLOWED_ORIGINS")
        .unwrap_or_default()
        .split(',')
        .filter(|s| !s.is_empty())
        .map(|s| s.parse().unwrap())
        .collect();

    let cors = CorsLayer::new()
        .allow_origin(AllowOrigin::list(allowed))
        .allow_credentials(true);

    // Mount versioned routers here, e.g. .nest("/v1", api::routes::v1())
    let app = Router::new()
        .route("/healthz", get(|| async { "ok" }))
        .layer(cors);

    let port: u16 = env::var("PORT").ok().and_then(|p| p.parse().ok()).unwrap_or(8080);
    let listener = tokio::net::TcpListener::bind(("0.0.0.0", port)).await.unwrap();
    tracing::info!("listening on :{}", port);
    axum::serve(listener, app).await.unwrap();
}

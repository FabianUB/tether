// Prevents additional console window on Windows in release
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod sidecar;

use sidecar::SidecarManager;
use std::sync::Arc;
use tauri::Manager;
use tokio::sync::Mutex;

#[tauri::command]
async fn get_api_port(state: tauri::State<'_, Arc<Mutex<SidecarManager>>>) -> Result<u16, String> {
    let manager = state.lock().await;
    Ok(manager.port())
}

#[tauri::command]
async fn restart_backend(
    state: tauri::State<'_, Arc<Mutex<SidecarManager>>>,
) -> Result<String, String> {
    let mut manager = state.lock().await;
    manager.restart().await
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            let app_handle = app.handle().clone();

            // Find an available port
            let port = portpicker::pick_unused_port().expect("No available port");

            // Create sidecar manager
            let manager = Arc::new(Mutex::new(SidecarManager::new(port)));

            // Store in app state
            app.manage(manager.clone());

            // Start the sidecar
            tauri::async_runtime::spawn(async move {
                let mut manager = manager.lock().await;
                if let Err(e) = manager.start(&app_handle).await {
                    eprintln!("Failed to start API server: {}", e);
                }
            });

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::CloseRequested { .. } = event {
                let app_handle = window.app_handle().clone();
                tauri::async_runtime::block_on(async {
                    let state = app_handle.state::<Arc<Mutex<SidecarManager>>>();
                    let mut manager = state.lock().await;
                    if let Err(e) = manager.stop() {
                        eprintln!("Error stopping API server: {}", e);
                    }
                });
            }
        })
        .invoke_handler(tauri::generate_handler![get_api_port, restart_backend])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

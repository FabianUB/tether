//! Python sidecar process management.

use std::process::Command as StdCommand;
use tauri::AppHandle;
use tauri_plugin_shell::process::{CommandChild, CommandEvent};
use tauri_plugin_shell::ShellExt;

/// Manages the Python sidecar process.
pub struct SidecarManager {
    child: Option<CommandChild>,
    port: u16,
}

impl SidecarManager {
    /// Create a new sidecar manager with the specified port.
    pub fn new(port: u16) -> Self {
        Self { child: None, port }
    }

    /// Get the port the sidecar is running on.
    pub fn port(&self) -> u16 {
        self.port
    }

    /// Start the sidecar process.
    pub async fn start(&mut self, app: &AppHandle) -> Result<String, String> {
        if self.child.is_some() {
            return Ok("API server is already running".into());
        }

        println!("Starting API server on port {}...", self.port);

        let shell = app.shell();
        let (mut rx, child) = shell
            .sidecar("api")
            .map_err(|e| format!("Failed to create sidecar command: {}", e))?
            .args(["--port", &self.port.to_string()])
            .spawn()
            .map_err(|e| format!("Failed to spawn API server: {}", e))?;

        // Spawn a task to handle sidecar output
        tauri::async_runtime::spawn(async move {
            while let Some(event) = rx.recv().await {
                match event {
                    CommandEvent::Stdout(line) => println!("API: {}", String::from_utf8_lossy(&line)),
                    CommandEvent::Stderr(line) => {
                        eprintln!("API Error: {}", String::from_utf8_lossy(&line))
                    }
                    CommandEvent::Error(error) => eprintln!("API Process Error: {}", error),
                    CommandEvent::Terminated(status) => {
                        println!("API Process Terminated with status: {:?}", status)
                    }
                    _ => {}
                }
            }
        });

        self.child = Some(child);
        println!("API server started successfully on port {}", self.port);
        Ok(format!("API server started on port {}", self.port))
    }

    /// Stop the sidecar process.
    pub fn stop(&mut self) -> Result<String, String> {
        if let Some(child) = self.child.take() {
            println!("Stopping API server...");

            let pid = child.pid();

            // Kill child processes first
            #[cfg(unix)]
            {
                let _ = StdCommand::new("pkill")
                    .args(["-P", &pid.to_string()])
                    .output();
            }

            #[cfg(windows)]
            {
                let _ = StdCommand::new("taskkill")
                    .args(["/F", "/T", "/PID", &pid.to_string()])
                    .output();
            }

            // Kill the main process
            child
                .kill()
                .map_err(|e| format!("Failed to stop API server: {}", e))?;

            println!("API server stopped");
            Ok("API server stopped".into())
        } else {
            Ok("API server is not running".into())
        }
    }

    /// Restart the sidecar process.
    pub async fn restart(&mut self) -> Result<String, String> {
        // We can't restart without an app handle, so this is a placeholder
        // In practice, you'd store the app handle or use a different approach
        self.stop()?;
        Err("Restart requires app handle - use Tauri commands".into())
    }
}

impl Drop for SidecarManager {
    fn drop(&mut self) {
        let _ = self.stop();
    }
}

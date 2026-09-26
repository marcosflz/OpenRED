//! Router IPC shell <-> sidecar: errores JSON-RPC tipados y framing de respuestas.
//!
//! El contrato (congelado) define respuestas `{"id","result"}` y errores
//! `{"id","error":{code,message,detail}}` (ver `contracts/methods.md` §1).

use serde::Serialize;
use serde_json::Value;
use tauri::{AppHandle, Manager};

use crate::sidecar::{self, Incoming, Sidecar};

/// Código de error: no hay sidecar vivo (sin conexión con el motor).
pub const ERR_NOT_RUNNING: i64 = 1008;
/// Código de error: error interno del shell / timeout de la petición.
pub const ERR_INTERNAL: i64 = 2000;

/// Timeout de las peticiones normales al sidecar.
pub const REQUEST_TIMEOUT_SECS: u64 = 300;

/// Error JSON-RPC que cruza la frontera hacia el webview.
#[derive(Debug, Clone, PartialEq, Serialize, thiserror::Error)]
#[error("rpc error {code}: {message}")]
pub struct RpcError {
    pub code: i64,
    pub message: String,
    pub detail: Option<Value>,
}

impl RpcError {
    pub fn new(code: i64, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
            detail: None,
        }
    }

    pub fn with_detail(code: i64, message: impl Into<String>, detail: Option<Value>) -> Self {
        Self {
            code,
            message: message.into(),
            detail,
        }
    }

    /// El proceso del motor no está en ejecución (o no se puede escribir en su stdin).
    pub fn not_running(last_error: Option<String>) -> Self {
        let detail = last_error.map(|err| serde_json::json!({ "lastError": err }));
        Self {
            code: ERR_NOT_RUNNING,
            message: "El motor no está en ejecución".to_string(),
            detail,
        }
    }

    pub fn timeout(method: &str) -> Self {
        Self::with_detail(
            ERR_INTERNAL,
            format!("La petición '{method}' superó el timeout de {REQUEST_TIMEOUT_SECS} s"),
            Some(serde_json::json!({ "method": method, "timeoutSecs": REQUEST_TIMEOUT_SECS })),
        )
    }

    pub fn internal(message: impl Into<String>) -> Self {
        Self::new(ERR_INTERNAL, message)
    }

    /// Construye el error a partir del objeto `error` del contrato.
    pub fn from_engine_error(error: &Value) -> Self {
        let code = error
            .get("code")
            .and_then(Value::as_i64)
            .unwrap_or(ERR_INTERNAL);
        let message = error
            .get("message")
            .and_then(Value::as_str)
            .unwrap_or("Error desconocido del motor")
            .to_string();
        let detail = match error.get("detail") {
            None | Some(Value::Null) => None,
            Some(value) => Some(value.clone()),
        };
        Self {
            code,
            message,
            detail,
        }
    }
}

/// Punto de entrada del router: reenvía una petición al sidecar gestionado.
pub async fn request(app: &AppHandle, method: String, params: Value) -> Result<Value, RpcError> {
    let sidecar = app.state::<Sidecar>().inner().clone();
    sidecar.request(method, params).await
}

/// Interpreta una línea JSONL del sidecar como respuesta de una petición.
/// Devuelve `None` para eventos, líneas vacías o JSON que no es una respuesta.
///
/// Es la pieza de framing que verifican los tests del router; queda expuesta para
/// reutilizarla en diagnósticos o en futuros transports alternativos.
#[allow(dead_code)]
pub fn parse_response(line: &str) -> Option<Result<Value, RpcError>> {
    match sidecar::parse_line(line)? {
        Incoming::Response { result, error, .. } => Some(sidecar::response_result(result, error)),
        Incoming::Event { .. } => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_response_result_ok() {
        let value = parse_response(r#"{"id":1,"result":{"ok":true,"n":2}}"#)
            .expect("debe ser una respuesta")
            .expect("result debe ser Ok");
        assert_eq!(value["ok"], true);
        assert_eq!(value["n"], 2);
    }

    #[test]
    fn parse_response_error_frame() {
        let line = r#"{"id":7,"error":{"code":1004,"message":"Ya existe config.json","detail":{"path":"C:/x"}}}"#;
        let err = parse_response(line)
            .expect("debe ser una respuesta")
            .expect_err("error debe ser Err");
        assert_eq!(err.code, 1004);
        assert_eq!(err.message, "Ya existe config.json");
        assert_eq!(err.detail.unwrap()["path"], "C:/x");
    }

    #[test]
    fn parse_response_error_without_detail() {
        let err =
            parse_response(r#"{"id":2,"error":{"code":-32602,"message":"params inválidos"}}"#)
                .expect("respuesta")
                .expect_err("error");
        assert_eq!(err.code, -32602);
        assert_eq!(err.detail, None);
    }

    #[test]
    fn parse_response_ignores_events_and_garbage() {
        assert!(parse_response("").is_none());
        assert!(parse_response("   \n").is_none());
        assert!(parse_response("esto no es json").is_none());
        assert!(parse_response(r#"{"method":"event","params":{"name":"ready"}}"#).is_none());
        assert!(parse_response(r#"{"foo":1}"#).is_none());
    }

    #[test]
    fn parse_response_result_null_is_ok() {
        let value = parse_response(r#"{"id":3,"result":null}"#)
            .expect("respuesta")
            .expect("null es un result válido");
        assert_eq!(value, Value::Null);
    }

    #[test]
    fn rpc_error_serializes_code_message_detail() {
        let value = serde_json::to_value(RpcError::not_running(Some("boom".into()))).unwrap();
        assert_eq!(value["code"], ERR_NOT_RUNNING);
        assert!(value["message"].is_string());
        assert_eq!(value["detail"]["lastError"], "boom");
        assert!(
            value.get("detail").is_some(),
            "detail siempre presente (null si no hay)"
        );

        let value = serde_json::to_value(RpcError::new(ERR_INTERNAL, "x")).unwrap();
        assert_eq!(value["detail"], Value::Null);
    }

    #[test]
    fn rpc_error_from_engine_error_defaults() {
        let err = RpcError::from_engine_error(&serde_json::json!({ "message": "solo mensaje" }));
        assert_eq!(err.code, ERR_INTERNAL);
        assert_eq!(err.message, "solo mensaje");
        assert_eq!(err.detail, None);
    }
}

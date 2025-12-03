import sys
import threading
from typing import Any, Dict, Optional, Callable
import uvicorn

# ==============================================================================
# CONFIGURATION
# ==============================================================================
API_TITLE = "Microservice Gateway"
API_VERSION = "1.0.0"
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8099
# ==============================================================================

class APIGatewayMS:
    """
    The Gateway: A wrapper that exposes a local Python object as a REST API.
    
    Features:
    - Auto-generates Swagger UI at /docs
    - Threaded execution (non-blocking for UI apps)
    - CORS enabled by default (for React/Web frontends)
    """

    def __init__(self, backend_core: Any):
        """
        :param backend_core: The logic object to expose (e.g. an instance of SearchEngineMS)
        """
        self.core = backend_core
        self.server_thread = None
        
        # Lazy import to avoid hard crash if libs are missing
        try:
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            from pydantic import BaseModel
            self.FastAPI = FastAPI
            self.CORSMiddleware = CORSMiddleware
            self.BaseModel = BaseModel
            self._available = True
        except ImportError:
            print("CRITICAL: 'fastapi' or 'uvicorn' not installed.")
            print("Run: pip install fastapi uvicorn pydantic")
            self._available = False
            return

        self.app = self.FastAPI(title=API_TITLE, version=API_VERSION)
        
        # Enable CORS
        self.app.add_middleware(
            self.CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"]
        )
        
        # Setup Base Routes
        self._setup_system_routes()

    def _setup_system_routes(self):
        @self.app.get("/")
        def root():
            return {"status": "online", "service": API_TITLE}

        @self.app.get("/health")
        def health():
            return {"status": "healthy", "backend_type": type(self.core).__name__}

    def add_endpoint(self, path: str, method: str, handler: Callable):
        """
        Dynamically adds a route to the API.
        
        :param path: URL path (e.g., "/search")
        :param method: "GET" or "POST"
        :param handler: The function to run
        """
        if method.upper() == "POST":
            self.app.post(path)(handler)
        elif method.upper() == "GET":
            self.app.get(path)(handler)

    def start(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, blocking: bool = True):
        """
        Starts the Uvicorn server.
        """
        if not self._available: return

        def _run():
            print(f"🚀 API Gateway running at http://{host}:{port}")
            print(f"📄 Docs available at http://{host}:{port}/docs")
            uvicorn.run(self.app, host=host, port=port, log_level="info")

        if blocking:
            _run()
        else:
            self.server_thread = threading.Thread(target=_run, daemon=True)
            self.server_thread.start()

# --- Independent Test Block ---
if __name__ == "__main__":
    # 1. Define a Mock Backend (The "Core" Logic)
    class MockBackend:
        def search(self, query):
            return [f"Result for {query} 1", f"Result for {query} 2"]
        
        def echo(self, msg):
            return f"Echo: {msg}"

    backend = MockBackend()
    
    # 2. Init Gateway
    gateway = APIGatewayMS(backend)
    
    if gateway._available:
        # 3. Define Request Models (Pydantic) for strong typing in Swagger
        class SearchReq(gateway.BaseModel):
            query: str
            limit: int = 10

        class EchoReq(gateway.BaseModel):
            message: str

        # 4. Map Backend Methods to API Endpoints
        
        def search_endpoint(req: SearchReq):
            """Searches the mock backend."""
            return {"results": backend.search(req.query), "limit": req.limit}
            
        def echo_endpoint(req: EchoReq):
            """Echoes a message."""
            return {"response": backend.echo(req.message)}

        gateway.add_endpoint("/v1/search", "POST", search_endpoint)
        gateway.add_endpoint("/v1/echo", "POST", echo_endpoint)

        # 5. Run
        # Note: In a real app, you might want blocking=False if running a UI too
        gateway.start(port=8099, blocking=True)
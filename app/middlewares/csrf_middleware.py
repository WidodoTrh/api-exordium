from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse

class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method == "OPTIONS":
            origin = request.headers.get("origin")
            return JSONResponse(
                status_code=200,
                content={},
                headers={
                    "Access-Control-Allow-Origin": origin or "*",
                    "Access-Control-Allow-Credentials": "true",
                    "Access-Control-Allow-Headers": "Content-Type, X-CSRF-TOKEN, x-requested-with",
                    "Access-Control-Allow-Methods": "GET, POST, PUT, PATCH, DELETE, OPTIONS",
                }
            )
            
        if request.url.path.startswith("/auth"):
            return await call_next(request)
        
        ngetest_doang = ['/data/data']
        
        if request.method in ("POST", "PUT", "PATCH", "DELETE") or request.url.path in ngetest_doang:
            csrf_cookie = request.cookies.get("XSRF-TOKEN")
            csrf_header = request.headers.get("X-CSRF-TOKEN")

            if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Your CSRF is not valid"},
                )
        response = await call_next(request)
        return response


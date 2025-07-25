# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# absolute import, now that backend is a package
from backend.routers import products, users, orders, inspection, models, analytics, admin, tutorials, orientations
# OR use relative import:
# from .routers import products, users, orders, inspection

app = FastAPI(
    title="StitchGuard API", 
    version="1.0.0",
    description="Quality assurance API for fabric inspection with ML integration"
)

# CORS middleware for iOS app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your iOS app's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
routers = [
    products.router,
    users.router,
    orders.router,
    inspection.router,
    models.router,
    analytics.router,
    admin.router,  # NEW: Admin endpoints including migration
    tutorials.router,  # NEW: Tutorial endpoints
    orientations.router  # NEW: Orientation management endpoints
]

for router in routers:
    app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "status": "OK",
        "message": "StitchGuard API is running - DEPLOYMENT TEST 2025-06-26",
        "version": "1.0.0",
        "docs": "/docs",
        "latest_commit": "b5dc4b3"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
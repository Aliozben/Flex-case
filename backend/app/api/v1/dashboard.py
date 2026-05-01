from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, List
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user
from app.models.auth import AuthenticatedUser
from sqlalchemy import text

router = APIRouter()

@router.get("/properties")
async def get_tenant_properties(
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context is required to fetch properties",
        )
    
    try:
        from app.core.database_pool import DatabasePool
        db_pool = DatabasePool()
        await db_pool.initialize()
        
        if db_pool.session_factory:
            async with db_pool.get_session() as session:
                query = text("SELECT id, name FROM properties WHERE tenant_id = :tenant_id")
                result = await session.execute(query, {"tenant_id": tenant_id})
                return [{"id": row.id, "name": row.name} for row in result]
        else:
            raise Exception("Database pool not available")
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching properties: {str(e)}"
        )


@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user)
) -> Dict[str, Any]:
    tenant_id = current_user.tenant_id
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant context is required for dashboard access",
        )
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)
    
    return {
        "property_id": revenue_data['property_id'],
        "total_revenue": revenue_data['total'],
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }


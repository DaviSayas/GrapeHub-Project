"""Reusable FastAPI dependencies: current user, role guards, db session."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.enums import UserRole
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# Re-export get_db so API routers can import from here
__all__ = ["get_db", "get_current_user", "require_admin"]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate JWT and return the authenticated user. Raises 401 on failure."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não autenticado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise exc

    payload = decode_access_token(token)
    if not payload:
        raise exc

    user_id = payload.get("sub")
    if not user_id:
        raise exc

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.active:
        raise exc
    return user


def require_roles(*allowed: UserRole):
    """Factory: dependency that restricts access to given roles."""
    allowed_values = {r.value for r in allowed}

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_values:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sem permissões para esta operação",
            )
        return user

    return _checker


require_admin = require_roles(UserRole.ADMIN)

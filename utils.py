from fastapi import HTTPException, status

def get_user_credentials_from_session(request, session_key="access_token"):
    session = request.session
    access_token = session.get(session_key)
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return access_token

# OAuth & Security Documentation

**Last Updated:** October 2026

This document outlines security requirements, best practices, and implementation guidance for Superior Spotify's authentication, token management, and data privacy.

---

## What We Know from Planning Docs

### Security-Relevant Requirements

From `planning/comprehensive-plan.md` and `planning/architecture.md`:

| Area | Requirement |
|------|-------------|
| **OAuth Integration** | Spotify OAuth 2.0 with refresh token flow |
| **Token Storage** | Access tokens and refresh tokens stored in PostgreSQL |
| **User Data** | Must protect listening history, preferences, and profile data |
| **API Access** | Backend serves as OAuth client protecting Spotify API calls |
| **Multi-User Support** | Each user's data must be isolated and secure |

### OAuth Scopes Required (from planning)

```
user-read-private          # Read user profile (display name, country)
user-read-email            # Read user email for account
user-read-recently-played  # Read Spotify's limited play history (20-50 tracks)
playlist-read-private      # Read user's private playlists
playlist-modify-public     # Create/edit public playlists
playlist-modify-private    # Create/edit private playlists
user-library-modify        # Save/unsave tracks to/from library
user-modify-playback-state # Control Spotify playback (play, pause, skip)
```

---

## Sources

### Planning Documents Referenced

- `planning/comprehensive-plan.md` - OAuth Scope section (lines 527-538), Data Flow architecture (lines 21-35)
- `planning/architecture.md` - Database schema for User tokens (lines 156-165), OAuth scope definitions (lines 89-99)

### Code Files Reviewed

- `app/services/auth.py` - JWT token creation and decoding
- `app/routers/auth.py` - OAuth login/callback flow
- `app/models.py` - User model with token storage (lines 45-48)
- `app/config.py` - Configuration with JWT secret handling

### Security Best Practices Referenced

- Spotify Web API Security: https://developer.spotify.com/documentation/web-api/concepts/security
- OAuth 2.0 RFC 6749
- OWASP Authentication Cheat Sheet
- JWT Security Best Practices (RFC 8725)

---

## OAuth Flow Security

### Current Implementation Analysis

The OAuth flow in `app/routers/auth.py` implements the Authorization Code flow:

```
1. /auth/login → Redirect to Spotify OAuth
2. /auth/callback → Handle code exchange, get tokens
3. Store tokens in database for user
```

### Security Best Practices for Spotify OAuth

#### 1. Use PKCE (Proof Key for Code Exchange)

**Current Gap:** The implementation does not use PKCE, which adds protection against authorization code interception attacks.

**Recommendation:** Implement PKCE for all OAuth flows:

```python
import secrets
import hashlib
import base64

def generate_pkce_pair():
    """Generate PKCE code verifier and challenge"""
    # 32-96 character random string
    code_verifier = secrets.token_urlsafe(32)
    
    # SHA256 hash of verifier, base64url encoded
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip('=')
    
    return code_verifier, code_challenge
```

#### 2. Short-Lived Authorization Codes

Spotify authorization codes are single-use and expire quickly. Ensure:
- Codes are exchanged immediately upon callback
- Codes are never stored longer than necessary
- Code exchange happens over HTTPS in production

#### 3. State Parameter for CSRF Protection

**Recommendation:** Always use the `state` parameter:

```python
import secrets
from functools import lru_cache
from cachetools import TTLCache

# Store state with timestamp, expire after 10 minutes
csrf_states = TTLCache(maxsize=1000, ttl=600)

@router.get("/login")
async def login(request: Request):
    state = secrets.token_urlsafe(16)
    csrf_states[state] = datetime.utcnow()
    
    # Store state in session or secure cookie
    request.session["oauth_state"] = state
    
    auth_url = spotify_service.get_auth_url(state=state)
    return RedirectResponse(url=auth_url)

@router.get("/callback")
async def callback(request: Request, code: str, state: str):
    # Validate state
    if state not in csrf_states:
        raise HTTPException(400, "Invalid state parameter")
    
    del csrf_states[state]  # One-time use
    # Continue with exchange
```

#### 4. Redirect URI Validation

**Current Implementation:** Uses configurable `SPOTIFY_REDIRECT_URI`

**Best Practice:** Whitelist exact redirect URIs, never accept dynamic URIs:

```python
# app/config.py
from typing import List

class Settings(BaseSettings):
    spotify_redirect_uris: List[str] = [
        "http://localhost:8000/callback",  # Development
        "https://yourdomain.com/callback"   # Production
    ]
```

---

## Token Storage

### Current Implementation

Tokens are stored directly in the `users` table:

```python
# app/models.py
access_token: Mapped[str] = mapped_column(Text, nullable=False)
refresh_token: Mapped[str] = mapped_column(Text, nullable=True)
token_expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
```

### Security Concerns

| Issue | Risk Level | Description |
|-------|------------|-------------|
| Plain text storage | HIGH | Tokens stored without encryption at rest |
| No token rotation | MEDIUM | Refresh tokens should rotate on use |
| No token binding | MEDIUM | Tokens not bound to device/session |

### Recommended Improvements

#### 1. Encrypt Tokens at Rest

**Recommendation:** Use application-layer encryption for sensitive tokens:

```python
from cryptography.fernet import Fernet
import os

class TokenEncrypter:
    def __init__(self):
        # Key should be from secure environment variable
        key = os.getenv("TOKEN_ENCRYPTION_KEY")
        if not key:
            raise RuntimeError("TOKEN_ENCRYPTION_KEY not configured")
        self.cipher = Fernet(key.encode())
    
    def encrypt_token(self, token: str) -> str:
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        return self.cipher.decrypt(encrypted_token.encode()).decode()
```

**Database Schema Update:**

```sql
-- Keep columns the same, but store encrypted values
ALTER TABLE users 
MODIFY COLUMN access_token TEXT ENCRYPTED,
MODIFY COLUMN refresh_token TEXT ENCRYPTED;
```

#### 2. Secure Key Management

```bash
# Generate encryption key (store securely, e.g., AWS Secrets Manager, HashiCorp Vault)
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

#### 3. Token Refresh Strategy

**Implement proactive token refresh:**

```python
# app/services/token_manager.py
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, db_session):
        self.db = db_session
    
    async def get_valid_token(self, user: User) -> str:
        """Return valid access token, refreshing if necessary"""
        
        # Refresh if within 5 minutes of expiration
        refresh_threshold = datetime.utcnow() + timedelta(minutes=5)
        
        if user.token_expires_at <= refresh_threshold:
            await self.refresh_token(user)
        
        return user.access_token
    
    async def refresh_token(self, user: User):
        """Refresh access token using refresh token"""
        if not user.refresh_token:
            raise AuthenticationError("No refresh token available")
        
        # Call Spotify token refresh endpoint
        new_token_info = await spotify_service.refresh_access_token(
            user.refresh_token
        )
        
        # Update user with new tokens
        user.access_token = new_token_info["access_token"]
        user.refresh_token = new_token_info.get("refresh_token", user.refresh_token)
        user.token_expires_at = datetime.utcnow() + timedelta(
            seconds=new_token_info["expires_in"]
        )
        
        await self.db.commit()
```

#### 4. Token Binding (Advanced)

For additional security, bind tokens to session/device:

```python
# Store device fingerprint with token
user.device_fingerprint = hash_user_agent(request.headers.get("user-agent"))

# Verify on subsequent requests
if user.device_fingerprint != current_fingerprint:
    raise SecurityError("Potential token compromise detected")
```

---

## JWT Security

### Current Implementation

`app/services/auth.py` provides basic JWT token handling:

```python
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
    return encoded_jwt
```

### JWT Security Recommendations

#### 1. Strengthen JWT Configuration

```python
# Recommended settings
ALGORITHM = "HS256"                    # Keep HS256 for simplicity, or migrate to RS256
ACCESS_TOKEN_EXPIRE_MINUTES = 15       # Shorter lifespan in production
REFRESH_TOKEN_EXPIRE_DAYS = 30         # Longer lifespan for refresh tokens

# Minimum JWT secret strength
JWT_SECRET_KEY_MIN_LENGTH = 32         # At least 256 bits of entropy
```

#### 2. Add Token Audience and Issuer Claims

```python
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Create JWT access token with security claims"""
    to_encode = data.copy()
    
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({
        "exp": expire,                      # Expiration time
        "iat": datetime.utcnow(),           # Issued at
        "nbf": datetime.utcnow(),           # Not before
        "jti": str(uuid.uuid4()),           # JWT ID (unique token ID)
        "iss": "superior-spotify",         # Issuer
        "aud": "superior-spotify-client",  # Audience
    })
    
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=ALGORITHM)
```

#### 3. JWT Secret Key Management

**Current:** `jwt_secret_key = "change-this-in-production"`

**Critical:** The JWT secret must be properly configured:

```bash
# Generate secure JWT secret
openssl rand -hex 32

# Or for 512-bit key (HS512)
openssl rand -hex 64
```

**Minimum Requirements:**
- Minimum 256 bits (32 bytes) of entropy
- Stored only in environment variables
- Never committed to version control

#### 4. Token Validation with Audience

```python
from jose import jwt, JWTError

def decode_access_token(token: str, verify_aud: bool = True) -> Optional[dict]:
    """Decode and validate JWT with security checks"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[ALGORITHM],
            options={
                "verify_exp": True,
                "verify_iat": True,
                "verify_nbf": True,
                "verify_aud": verify_aud,
            },
            audience="superior-spotify-client"
        )
        return payload
    except JWTError as e:
        # Log security event for failed validation
        logger.warning(f"JWT validation failed: {e}")
        return None
```

---

## Data Privacy

### Data We Collect

| Data Type | Purpose | Retention | Sensitivity |
|-----------|---------|-----------|-------------|
| Spotify profile (name, email) | User identification | Account lifetime | Low |
| OAuth tokens | API authentication | Account lifetime | **High** |
| Listening events | Analytics, recommendations | Account lifetime | **Medium-High** |
| Audio feature preferences | Personalization | Account lifetime | Low-Medium |
| Playlist data | Content generation | Account lifetime | Medium |

### Privacy Best Practices

#### 1. Data Minimization

- Collect only data required for core functionality
- Do not track personally identifiable information beyond Spotify ID
- Provide data export functionality (GDPR requirement)

#### 2. Data Access Controls

```python
# Always verify user owns the data they access
async def get_listening_events(user: User, db: AsyncSession):
    statement = select(ListeningEvent).where(
        ListeningEvent.user_id == user.id
    )
    # Never query by ID without ownership check
    # SQL injection protected by parameterized queries
```

#### 3. Secure API Communication

**Require HTTPS in production:**

```python
# FastAPI middleware for HTTPS redirect
from fastapi.middleware import httpsredirect

app.add_middleware(httpsredirect.HTTPSRedirectMiddleware)
```

#### 4. Cookie Security (for session-based auth)

```python
# Secure cookie settings
def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="auth_token",
        value=token,
        httponly=True,        # Prevent JavaScript access
        secure=True,          # HTTPS only
        samesite="lax",       # CSRF protection
        max_age=3600,         # 1 hour
        path="/"
    )
```

### User Rights (GDPR Compliance)

Implement these endpoints:

```python
@router.post("/user/export")
async def export_user_data(user: User):
    """Export all user data (GDPR Article 15)"""
    # Return all listening events, preferences, playlists

@router.delete("/user/data")
async def delete_user_data(user: User):
    """Delete all user data (GDPR Article 17)"""
    # Soft delete or hard delete based on preference

@router.get("/user/privacy-settings")
async def get_privacy_settings(user: User):
    """Return user's privacy configuration"""
    # What data is tracked, sharing preferences
```

---

## Required OAuth Scopes

### Detailed Scope Breakdown

| Scope | Purpose | Necessity |
|-------|---------|-----------|
| `user-read-private` | Read user's display name, country | **Required** - User identification |
| `user-read-email` | Read user's email | **Required** - Account management |
| `user-read-recently-played` | Get 20-50 most recent plays | Optional - Limited utility, we self-track |
| `playlist-read-private` | Access private playlists | **Required** - Read user's saved playlists |
| `playlist-modify-public` | Create public playlists | Optional - For sharing feature |
| `playlist-modify-private` | Create private playlists | **Required** - Save smart playlists |
| `user-library-modify` | Save/unsave tracks | Optional - For recommendations |
| `user-modify-playback-state` | Control playback | Optional - For playback control feature |

### Scopes by Feature

| Feature | Required Scopes |
|---------|-----------------|
| User authentication | `user-read-private`, `user-read-email` |
| Self-tracking (MVP) | None (uses POST /listen endpoint) |
| Smart Playlists | `playlist-modify-private`, `playlist-read-private` |
| Playback Control | `user-modify-playback-state` |
| Social Features | `user-library-read` |

### OAuth Scope Request URL

```python
def get_auth_url(self, state: Optional[str] = None) -> str:
    """Generate Spotify OAuth authorization URL"""
    scopes = [
        "user-read-private",
        "user-read-email",
        "playlist-read-private",
        "playlist-modify-private",
    ]
    
    query_params = {
        "client_id": self.client_id,
        "response_type": "code",
        "redirect_uri": self.redirect_uri,
        "scope": " ".join(scopes),
        "state": state or secrets.token_urlsafe(16),
    }
    
    # Add PKCE challenge if using PKCE
    # query_params["code_challenge"] = code_challenge
    # query_params["code_challenge_method"] = "S256"
    
    return f"https://accounts.spotify.com/authorize?{urlencode(query_params)}"
```

---

## Open Questions

### Unresolved Security Concerns

| Question | Priority | Notes |
|----------|----------|-------|
| Should we implement token rotation? | High | Spotify supports refresh token rotation |
| How to handle token revocation? | Medium | User may revoke access in Spotify settings |
| Browser extension security model? | Medium | If we build extension, CSP and permissions matter |
| Rate limit handling for token refresh? | Medium | Prevent DoS via refresh spam |
| Encryption key rotation strategy? | Medium | Key rotation for encrypted tokens |
| Cross-site request forgery (CSRF) tokens? | High | Session-based CSRF protection needed |

### Implementation Decisions Needed

1. **Session Management:** Session-based vs. token-based auth for user sessions?
2. **Token Storage Encryption:** Key management strategy (AWS KMS, HashiCorp Vault, or application key)?
3. **Privacy Default:** Should listening data be private by default with opt-in sharing?

---

## Implementation Recommendations

### Priority 1: Immediate (Before Any User Data)

- [ ] Generate secure JWT secret (`openssl rand -hex 64`)
- [ ] Store secrets in environment variables only
- [ ] Implement HTTPS redirect middleware
- [ ] Add CSRF protection with state parameter
- [ ] Validate redirect URIs against whitelist

### Priority 2: Near-Term (MVP Launch)

- [ ] Implement token encryption at rest
- [ ] Add proactive token refresh logic
- [ ] Implement HTTPS-only cookies
- [ ] Add audit logging for authentication events
- [ ] Implement user data export endpoint

### Priority 3: Production Hardening

- [ ] Implement PKCE for all OAuth flows
- [ ] Add rate limiting on auth endpoints
- [ ] Implement token binding by device fingerprint
- [ ] Set up centralized secrets management
- [ ] Add security headers (HSTS, CSP)

### Security Header Configuration

```python
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.security import SecurityMiddleware

# Security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    return response
```

### Security Testing Checklist

Before production launch:

- [ ] Test OAuth flow without state parameter (should fail)
- [ ] Test token tampering (should reject)
- [ ] Verify tokens are not logged
- [ ] Verify HTTPS redirects in production
- [ ] Test rate limiting on auth endpoints
- [ ] Verify database encryption at rest
- [ ] Perform dependency security audit (`pip-audit` or `safety check`)

---

## References

- [Spotify Web API Security](https://developer.spotify.com/documentation/web-api/concepts/security)
- [OAuth 2.0 RFC 6749](https://tools.ietf.org/html/rfc6749)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [JWT Security Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)

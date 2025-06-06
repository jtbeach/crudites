"""Auth0 integration."""

from collections.abc import Sequence

import jwt
from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, SecurityScopes
from pydantic import BaseModel


class Auth0Config(BaseModel):
    """Auth0 configuration."""

    domain: str
    leeway: int = 5
    algorithms: list[str] = ["RS256"]


class Auth0Token(BaseModel):
    """Model represented data stored in Auth0 JWT access token.

    Normally applications would subclass this to add fields for custom claims, etc.
    that might be application-specific.
    """

    iss: str
    sub: str
    aud: str | Sequence[str]
    iat: int
    exp: int


#
# FastAPI-Auth0 security integration
#


class UnauthorizedException(HTTPException):
    """Exception raised when a token is not authorized."""

    def __init__(self, detail: str, **kwargs):
        """Returns HTTP 403."""
        super().__init__(status.HTTP_403_FORBIDDEN, detail=detail)


class UnauthenticatedException(HTTPException):
    """Exception raised when a token is missing or can't be authenticated."""

    def __init__(self):
        """Returns HTTP 401."""
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Requires authentication"
        )


class Auth0TokenVerifier[TokenT: Auth0Token, ConfigT: Auth0Config]:
    """Auth0 token verifier.

    Inspired by https://auth0.com/blog/build-and-secure-fastapi-server-with-auth0/
    """

    def __init__(
        self,
        config: ConfigT,
        token_model_cls: type[TokenT],
        allowed_audiences: list[str],
    ) -> None:
        """Constructor."""
        self.config = config
        self.token_model_cls = token_model_cls
        self.allowed_audiences: list[str] = allowed_audiences

        # This gets the JWKS from a given URL and does processing so you can
        # use any of the keys available
        jwks_url = f"https://{self.config.domain}/.well-known/jwks.json"
        self.jwks_client = jwt.PyJWKClient(jwks_url)

    async def verify(
        self,
        security_scopes: SecurityScopes,
        http_authorization_credentials: HTTPAuthorizationCredentials | None,
    ) -> TokenT:
        """Verify an Auth0-issued JWT token send as a bearer token and return the payload.

        Signature matches what is expected by the FastAPI Security scheme.
        """

        if http_authorization_credentials is None:
            raise UnauthenticatedException

        bearer_token = http_authorization_credentials.credentials

        try:
            signing_key = await run_in_threadpool(
                self.jwks_client.get_signing_key_from_jwt,
                bearer_token,
            )
        except jwt.exceptions.PyJWKClientError as error:
            raise UnauthorizedException(str(error)) from error
        except jwt.exceptions.DecodeError as error:
            raise UnauthorizedException(str(error)) from error

        try:
            payload = jwt.decode(
                bearer_token,
                signing_key.key,
                algorithms=self.config.algorithms,
                issuer=f"https://{self.config.domain}/",
                leeway=self.config.leeway,
                audience=self.allowed_audiences,
                options={
                    "require": ["iss", "sub", "aud", "iat", "exp"],
                    "verify_signature": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                },
            )

            return self.token_model_cls(**payload)
        except Exception as error:
            raise UnauthorizedException(str(error)) from error

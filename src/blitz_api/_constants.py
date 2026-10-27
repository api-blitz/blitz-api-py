"""Internal defaults shared by the sync and async clients."""

from __future__ import annotations

from ._version import __version__

#: Production API base URL.
DEFAULT_BASE_URL = "https://api.blitz-api.ai"

#: Environment variable read when ``api_key`` is not passed explicitly.
API_KEY_ENV_VAR = "BLITZ_API_KEY"

#: Header carrying the API key (Blitz uses ``x-api-key``, not ``Authorization``).
API_KEY_HEADER = "x-api-key"

#: Default per-request timeout, in seconds.
DEFAULT_TIMEOUT = 30.0

#: Number of retries (in addition to the first attempt) for transient failures.
DEFAULT_MAX_RETRIES = 3

#: Default client-side rate limit, applied **per endpoint** (one sliding window each).
#: The API limits each endpoint independently, per account, at a rate set by the plan: 5 req/s
#: on the free trial, 10 on Start, 25 on Scale, custom on Build Your Infra (50 on plans created
#: before 2026-09-30). This default is the free-trial limit, so it leaves throughput on the
#: table on paid plans: raise it to your key's actual per-endpoint value, discoverable via
#: ``client.account.key_info().max_requests_per_seconds``.
DEFAULT_RATE_LIMIT_RPS = 5.0

#: Seconds to wait after a 429 when the response has no ``Retry-After`` header.
#: Matches the behaviour of the official reference client.
DEFAULT_RETRY_AFTER_SECONDS = 60.0

#: Upper bound (seconds) on any single retry wait, including a server-supplied
#: ``Retry-After``. A safety clamp so a pathological header value (e.g.
#: ``Retry-After: 86400``) can't make the client sleep for hours.
MAX_RETRY_WAIT_SECONDS = 120.0

#: Sent as the ``User-Agent`` header so requests are attributable to this SDK.
USER_AGENT = f"blitz-api-py/{__version__}"

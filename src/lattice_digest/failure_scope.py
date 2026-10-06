from enum import StrEnum


class FailureScope(StrEnum):
    QUERY_LOCAL = 'QUERY_LOCAL'
    FAMILY_LOCAL = 'FAMILY_LOCAL'
    PROVIDER_WIDE = 'PROVIDER_WIDE'
    RATE_LIMIT_DEFERRED = 'RATE_LIMIT_DEFERRED'
    TRANSPORT_FAILURE = 'TRANSPORT_FAILURE'
    MALFORMED_RESPONSE = 'MALFORMED_RESPONSE'


def failure_scope(category: str) -> FailureScope:
    if category == 'time_budget':
        return FailureScope.FAMILY_LOCAL
    if category in {'invalid_request', 'not_acceptable', 'empty_query', 'invalid_query'}:
        return FailureScope.QUERY_LOCAL
    if category == 'rate_limit':
        return FailureScope.RATE_LIMIT_DEFERRED
    if category in {'timeout', 'ssl_error', 'network_error', 'connection_error'}:
        return FailureScope.TRANSPORT_FAILURE
    if category in {'malformed_response', 'parse_error'}:
        return FailureScope.MALFORMED_RESPONSE
    return FailureScope.PROVIDER_WIDE

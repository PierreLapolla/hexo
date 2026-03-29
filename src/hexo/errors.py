class HexoError(Exception):
    """
    Represent the base exception for all Hexo engine failures.

    This exception is used as the root class for domain-specific errors raised
    by the package so callers can catch all Hexo-related exceptions with one type.
    """


class IllegalTurnError(HexoError):
    """
    Signal that a move or turn violates Hexo game rules.

    This exception is raised when validation fails during state reconstruction,
    move application, or other rule-checked operations.
    """

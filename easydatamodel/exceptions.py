class InvalidFieldError(Exception):
    """
    Raised when an easydatamodel Field has an invalid configuration.
    """

    pass


class InvalidModelError(Exception):
    """
    Raised when an easydatamodel Model has an invalid configuration or encounters an error during creation.
    """

    pass

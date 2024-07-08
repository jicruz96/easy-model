class InvalidFieldError(Exception):
    """
    Raised when an easy_model Field has an invalid configuration.
    """

    pass


class InvalidModelError(Exception):
    """
    Raised when an easy_model Model has an invalid configuration or encounters an error during creation.
    """

    pass

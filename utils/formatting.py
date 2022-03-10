def to_float_format(qty: str) -> float:
    """The function converting qty to float type.

    Params
    ------
        qty : str
            The quantity of coins upcoming from the api.

    Returns
    -------
        qty : float
            The quantity of coins upcoming from the api but converted to float type.
    """

    return float("{:0.2f}".format(qty))

def to_integer_format(qty: str) -> int:
    """The function converting qty to integer type.

    Params
    ------
        qty : str
            The quantity of coins upcoming from the api.

    Returns
    -------
        qty : float
            The quantity of coins upcoming from the api but converted to integer type.
    """

    return int(float("{:0.2f}".format(qty)))
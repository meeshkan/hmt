import warnings


def ignore_warnings():
    """Several of our deps have deprecation warnings
    # we ignore for now, but should look into."""
    ### This comes from faust """
    warnings.filterwarnings(
        action="ignore", category=DeprecationWarning, module=r"venusian"
    )
    ### This comes from lenses
    warnings.filterwarnings(
        action="ignore", category=DeprecationWarning, module=r"singledispatch_helpers"
    )

def memoized(func):
    def MEMOIZER(*args, **kwargs):
        results = func(*args, **kwargs)
        retval = {"cache_return":True, "call_results": results}
        return retval

    if not func.__name__[0:1] == '_':
        MEMOIZER.__name_ = func.__name__
        MEMOIZER.__doc__ = func.__doc__
        MEMOIZER.__dict__.update(func.__dict__)
        #func.__dict__["memoizer"] = NEVER_SEEN
        #print func.__dict__
        return MEMOIZER
    else:
        return func

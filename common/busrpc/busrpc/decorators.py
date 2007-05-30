def memoized(func):
    if not func.__name__[0:1] == '_':
        if hasattr(func, '_header_generator'):
            generator = func._header_generator
            def decorator(headers):
                generator(header)
                headers['cache_results'] = '1'
            func._header_generator = decorator
        else:
            def decorator(headers):
                headers['cache_results'] = '1'
            func._header_generator = decorator
    return func

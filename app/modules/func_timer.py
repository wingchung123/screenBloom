from time import time


# Execution time decorator
def func_timer(func):
    # Nested function for timing other functions
    def function_timer(*args, **kwargs):
        start = time()
        value = func(*args, **kwargs)  # Nested function execution
        end = time()
        runtime = end - start
        # print(f'|| [Execution Time] {func.__name__}() {runtime:02.4f} seconds')
        return value
    return function_timer

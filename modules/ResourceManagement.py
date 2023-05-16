
def fit_resource(new_value, limit_value):
    try:
        return min(limit_value / new_value, 1)
    except ZeroDivisionError:
        return 1

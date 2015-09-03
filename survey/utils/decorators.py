

def static_var(varName, value):
    def decorate(function):
        setattr(function,varName,value)
        return function
    return decorate
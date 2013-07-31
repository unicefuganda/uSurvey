import sys
if ('test' in sys.argv) or ('harvest' in sys.argv):
    from johnny.cache import enable
    enable()
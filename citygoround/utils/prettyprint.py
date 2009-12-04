def pretty_print_time_elapsed(float_time):
    return "%d days %d hours" %(float_time/(3600*24),(float_time%(3600*24))/3600)

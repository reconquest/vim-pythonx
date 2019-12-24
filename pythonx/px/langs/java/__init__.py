
def get_var_name_by_class_name(name):
    if name == "ActiveObjects":
        return "ao"

    if len(name) > 0:
        name = name[0].lower() + name[1:]
    return name

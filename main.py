import generator
generator.make_config("test", extract=False, install=False)
print(generator.make_abstract("test"))
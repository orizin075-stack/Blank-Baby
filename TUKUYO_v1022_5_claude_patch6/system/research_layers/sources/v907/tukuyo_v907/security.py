FORBIDDEN=('open(','pathlib','os.','subprocess','socket','requests','__import__','import ')
def validate_source(src):
 low=src.lower();bad=[x for x in FORBIDDEN if x in low];return (not bad),bad

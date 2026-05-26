print('\n'.join([''.join(['*' if abs(sum([z**2 + complex(x / 40.0, y / 20.0) for z in [0]*20])) < 2 else ' ' for x in range(-40, 20)]) for y in range(-15, 15)]))

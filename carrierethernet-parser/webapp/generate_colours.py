import random

for i in range(100):
    r1 = lambda: random.randint(0,255)
    r2 = lambda: random.randint(0,255)
    r3 = lambda: random.randint(0,255)
    print('.ringcolor-%s { stroke: #%02X%02X%02X }' % (i, r1(),r2(),r3()))

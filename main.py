import os
import sys

print(__file__)
print(sys.argv)
while True:
    os.execv(sys.executable, ['python'] + ['chatbot.py'])

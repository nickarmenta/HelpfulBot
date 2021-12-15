with open('PickAndPlace.py','r') as f:
    programString = f.read()
    f.close()

programParsed = programString.replace('\n',' ').replace('  ',' ')

with open('PickAndPlace.script','w') as f:
    f.write(programParsed)

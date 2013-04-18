from ase.cli import run
from ase.db import connect
from ase.db.json import read_json
from ase.calculators.nwchem import NWChem

run('O2 O run -c nwchem -d oxygen.json')
conn = connect('oxygen.json')
dct = read_json('oxygen.json')
for name in ['O2', 'O']:
    e1 = conn[name].get_potential_energy()
    e2 = NWChem.read_atoms(name).get_potential_energy()
    e3 = dct[name]['results']['energy']
    assert e1 == e2 == e3
    print(e1)
ae = 2 * dct['O']['results']['energy'] - dct['O2']['results']['energy']
assert abs(ae - 6.6053) < 1e-4

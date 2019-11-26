import os
import numpy as np

_special_kws = ['center', 'autosym', 'autoz', 'theory', 'basis', 'xc', 'task',
                'pseudopotentials', 'set', 'symmetry', 'label', 'geompar',
                'basispar']

_system_type = {1: 'polymer', 2: 'surface', 3: 'crystal'}


def _get_geom(atoms, **params):
    geom_header = ['geometry units angstrom']
    if not params.get('center', False):
        geom_header.append('nocenter')
    if not params.get('autosym', False):
        geom_header.append('noautosym')
    if not params.get('autoz', False):
        geom_header.append('noautoz')
    if 'geompar' in params:
        geom_header.append(params['geompar'])
    geom = [' '.join(geom_header)]

    outpos = atoms.get_positions()
    pbc = atoms.pbc
    if np.any(pbc):
        scpos = atoms.get_scaled_positions()
        for i, pbci in enumerate(pbc):
            if pbci:
                outpos[:, i] = scpos[:, i]
        npbc = pbc.sum()
        cellpars = atoms.get_cell_lengths_and_angles()
        geom.append('  system {} units angstrom'.format(_system_type[npbc]))
        if npbc == 3:
            geom.append('    lattice_vectors')
            for row in atoms.cell:
                geom.append('      {:20.16e} {:20.16e} {:20.16e}'.format(*row))
        else:
            if pbc[0]:
                geom.append('    lat_a {:20.16e}'.format(cellpars[0]))
            if pbc[1]:
                geom.append('    lat_b {:20.16e}'.format(cellpars[1]))
            if pbc[2]:
                geom.append('    lat_c {:20.16e}'.format(cellpars[2]))
            if pbc[1] and pbc[2]:
                geom.append('    alpha {:20.16e}'.format(cellpars[3]))
            if pbc[0] and pbc[2]:
                geom.append('    beta {:20.16e}'.format(cellpars[4]))
            if pbc[1] and pbc[0]:
                geom.append('    gamma {:20.16e}'.format(cellpars[5]))
        geom.append('  end')

    for i, atom in enumerate(atoms):
        geom.append('{:>4} {:20.16e} {:20.16e} {:20.16e}'
                    ''.format(atom.symbol, *outpos[i]))
        symm = params.get('symmetry')
        if symm is not None:
            geom.append('symmetry {}'.format(symm))
    geom.append('end')
    return geom


def _get_basis(**params):
    basis_in = params.get('basis', dict())
    if 'basispar' in params:
        header = 'basis {} noprint'.format(params['basispar'])
    else:
        header = 'basis noprint'
    basis_out = [header]
    if isinstance(basis_in, str):
        basis_out.append('   * library {}'.format(basis_in))
    else:
        for symbol, ibasis in basis_in.items():
            basis_out.append('{:>4} library {}'.format(symbol, ibasis))
    basis_out.append('end')
    return basis_out


_special_keypairs = [('nwpw', 'simulation_cell'),
                     ('nwpw', 'carr-parinello'),
                     ('nwpw', 'brillouin_zone'),
                     ('tddft', 'grad'),
                     ]


def _format_line(key, val):
    if val is None:
        return key
    if isinstance(val, bool):
        return '{} .{}.'.format(key, str(val).lower())
    else:
        return ' '.join([key, str(val)])


def _format_block(key, val, nindent=0):
    prefix = '  ' * nindent
    prefix2 = '  ' * (nindent + 1)
    if val is None:
        return [prefix + key]

    if not isinstance(val, dict):
        return [prefix + _format_line(key, val)]

    out = [prefix + key]
    for subkey, subval in val.items():
        if (key, subkey) in _special_keypairs:
            out += _format_block(subkey, subval, nindent + 1)
        else:
            if isinstance(subval, dict):
                subval = ' '.join([_format_line(a, b)
                                   for a, b in subval.items()])
            out.append(prefix2 + ' '.join([subkey, str(subval)]))
    out.append(prefix + 'end')
    return out


def _get_other(**params):
    out = []
    for kw, block in params.items():
        if kw in _special_kws:
            continue
        out += _format_block(kw, block)
    return out


def _get_set(**params):
    return ['set ' + _format_line(key, val) for key, val in params.items()]


def _get_theory(**params):
    theory = params.get('theory')
    if theory is not None:
        return theory
    nwpw = params.get('nwpw')
    xc = params.get('xc')
    if xc is None:
        if 'tce' in params:
            return 'tce'
        elif 'ccsd' in params:
            return 'ccsd'
        elif 'mp2' in params:
            return 'mp2'
        elif 'scf' in params:
            return 'scf'
        elif 'tddft' in params:
            return 'tddft'
        elif nwpw is not None:
            if 'monkhorst-pack' in nwpw or 'brillouin_zone' in nwpw:
                return 'band'
            return 'pspw'
        return 'scf'
    if xc in ['scf', 'dft', 'mp2', 'ccsd', 'tce', 'pspw', 'band', 'paw',
              'tddft']:
        return xc
    return 'dft'


_xc_conv = dict(lda='slater pw91lda',
                pbe='xpbe96 cpbe96',
                revpbe='revpbe cpbe96',
                rpbe='rpbe cpbe96',
                pw91='xperdew91 perdew91',
                )


def _update_mult(magmom_tot, **params):
    theory = params['theory']
    if magmom_tot == 0:
        magmom_mult = 1
    else:
        magmom_mult = np.sign(magmom_tot) * (abs(magmom_tot) + 1)
    if 'scf' in params:
        for kw in ['nopen', 'singlet', 'doublet', 'triplet', 'quartet',
                   'quintet', 'sextet', 'septet', 'octet']:
            if kw in params['scf']:
                break
        else:
            params['scf']['nopen'] = magmom_tot
    elif theory in ['scf', 'mp2', 'ccsd', 'tce']:
        params['scf'] = dict(nopen=magmom_tot)

    if 'dft' in params:
        if 'mult' not in params['dft']:
            params['dft']['mult'] = magmom_mult
    elif theory in ['dft', 'tddft']:
        params['dft'] = dict(mult=magmom_mult)

    if 'nwpw' in params:
        if 'mult' not in params['nwpw']:
            params['nwpw']['mult'] = magmom_mult
    elif theory in ['pspw', 'band', 'paw']:
        params['nwpw'] = dict(mult=magmom_mult)

    return params


def write_nwchem_in(fd, atoms, properties=None, **params):
    params = params.copy()
    label = params.get('label', 'nwchem')
    perm = os.path.abspath(params.get('perm', label))
    scratch = os.path.abspath(params.get('scratch', label))
    os.makedirs(perm, exist_ok=True)
    os.makedirs(scratch, exist_ok=True)

    if properties is None:
        properties = ['energy']

    task = params.get('task')
    if task is None:
        if 'forces' in properties:
            task = 'gradient'
        else:
            task = 'energy'

    theory = _get_theory(**params)
    params['theory'] = theory
    xc = params.get('xc')
    if 'xc' in params:
        xc = _xc_conv.get(params['xc'], params['xc'])
        if theory == 'dft':
            if 'dft' not in params:
                params['dft'] = dict()
            params['dft']['xc'] = xc
        elif theory in ['pspw', 'band', 'paw']:
            if 'nwpw' not in params:
                params['nwpw'] = dict()
            params['nwpw']['xc'] = xc

    magmom_tot = int(atoms.get_initial_magnetic_moments().sum())
    params = _update_mult(magmom_tot, **params)

    out = ['title "{}"'.format(label),
           'permanent_dir {}'.format(perm),
           'scratch_dir {}'.format(scratch),
           'start {}'.format(label),
           '\n'.join(_get_geom(atoms, **params)),
           '\n'.join(_get_basis(**params)),
           '\n'.join(_get_other(**params)),
           '\n'.join(_get_set(**params.get('set', dict()))),
           'task {} {}'.format(theory, task)]

    fd.write('\n\n'.join(out))

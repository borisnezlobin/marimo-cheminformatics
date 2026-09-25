import base64, io, json, subprocess, sys, urllib.request
import numpy as np
from PIL import Image
from rdkit import Chem
from rdkit.Chem import AllChem

COLORS = {'med': ('#7FB6DA', '#5A97C2'), 'actor': ('#EFC94C', '#D9A92E')}

def rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return ','.join(f'{int(hex_color[i:i + 2], 16) / 255:.3f}' for i in (0, 2, 4))

def smiles_for(name):
    url = f'https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/property/IsomericSMILES/TXT'
    return urllib.request.urlopen(url).read().decode().splitlines()[0]

def write_pdb(name, smiles):
    mol = Chem.AddHs(Chem.MolFromSmiles(smiles))
    AllChem.EmbedMolecule(mol, randomSeed=7)
    AllChem.MMFFOptimizeMolecule(mol)
    block = Chem.MolToPDBBlock(Chem.RemoveHs(mol)).replace('UNL', 'LIG').replace('ATOM  ', 'HETATM')
    open(f'{name}.pdb', 'w').write(block)

def render(name, role):
    light, dark = COLORS[role]
    command = f"""read
{name}.pdb
HETATM-C-------- 0,9999, {rgb(light)}, 1.6
HETATM---------- 0,9999, {rgb(dark)}, 1.5
END
center
auto
trans
0.,0.,0.
scale
4.0
wor
1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0
1,0.0023,2.0,1.0,0.2
-12,-12
illustrate
3.0,10.0,4,0.0,5.0
3.0,10.0
3.0,8.0,6000.
calculate
{name}_{role}.pnm
"""
    subprocess.run(['./illus'], input=command.encode(), capture_output=True, check=True)
    pixels = np.array(Image.open(f'{name}_{role}.pnm').convert('RGB'))
    alpha = np.where((pixels == 255).all(-1), 0, 255).astype(np.uint8)
    image = Image.fromarray(np.dstack([pixels, alpha]))
    image = image.resize((round(image.width * 0.9), round(image.height * 0.9)), Image.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buffer.getvalue()).decode()

requests = [arg.split(':') for arg in sys.argv[1:]]
sprites = {}
for name, role in requests:
    write_pdb(name, smiles_for(name))
    sprites[name + ('_med' if role == 'med' else '')] = render(name, role)
json.dump(sprites, open('new_sprites.json', 'w'))
print({key: len(value) // 1024 for key, value in sprites.items()})

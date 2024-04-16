import argparse
import os
from subprocess import Popen
from pathlib import Path
import shutil

MEDIABENCH = ['adpcmdecode', 'adpcmencode', 'epic', 'unepic', 'g721decode', 'g721encode', 'ghostsript', 'gsmdecode', 'gsmencode', 'jpegdecode', 'jpegencode', 'mesamipmap', 'mesaosdemo', 'mesatexgen', 'mpeg2decode', 'mpeg2encode']
MIBENCH_DICT = {'automotive': ['basicmath', 'bitcount', 'qsort', 'susans', 'susane', 'susanc'], 'consumer': ['jpegc', 'jpegd', 'lame', 'mad', 'typeset'], 'network': ['dijkstra', 'patricia'], 'office': ['ghostscriptstatic', 'rsynth', 'sphinx', 'stringsearch'], 'security': ['blowfishd', 'blowfishe', 'rijndaeld', 'rijndaele', 'sha'], 'telecomm': ['adpcmdecodestatic', 'adpcmencodestatic', 'crc32', 'fft', 'ffti', 'gsmdecodestatic', 'gsmencodestatic']}

MIBENCH = []
for x in MIBENCH_DICT.values():
    MIBENCH.extend(x)

RESOURCES = MEDIABENCH + MIBENCH
print(f'Number of resources: {len(RESOURCES)}.')

parser = argparse.ArgumentParser(description="Batch running gem5 simulations.")
parser.add_argument('-j', type=int, default=32, help='Number of parallel jobs.')
args = parser.parse_args()

def Pcheck():
    if len(sub_proc) < args.j: return True
    while True:
        for i, (p, out, err) in enumerate(sub_proc):
            ret = p.poll()
            if ret is not None:
                out.close()
                err.close()
                if ret != 0:
                    print(f'Error exit code {ret} from subprocess {p.args}.')
                sub_proc.pop(i)
                return True

cwd = Path.cwd()
os.environ['GEM5_CONFIG'] = str(cwd / 'config.json')
output_dir = cwd / 'output'

gem5 = '/home/fjtcin/Documents/gem5/build/ARM/gem5.opt'
sub_proc = []

for i in range(1, 11):
    if i == 3: width = '4'
    else: width = '8'

    if i == 4: freq = '4GHz'
    else: freq = '1GHz'

    if i == 5: l1dsize = l1isize = '64KiB'
    else: l1dsize = l1isize = '32KiB'
    if i == 6: l2size = '2MiB'
    else: l2size = '1MiB'

    if i == 9: l1dassoc = l1iassoc = '4'
    else: l1dassoc = l1iassoc = '2'
    if i == 10: l2assoc = '4'
    else: l2assoc = '16'

    if i == 2: l1dmshr = '2'
    else: l1dmshr = '6'
    l1imshr = '2'
    l2mshr = '16'

    if i == 8: l2policy = 'LRU'
    else: l2policy = 'Random'

    if i == 7: cache_line = '128'
    else: cache_line = '64'

    for resource in RESOURCES:
        work_dir = output_dir / str(i) / resource
        out_file = work_dir / 'out.txt'
        if out_file.exists():
            with open(out_file) as f:
                lines = f.readlines()
                if lines and 'Exiting @ tick' in lines[-1] and 'because exiting with last active thread context.' in lines[-1]:
                    print(f'Skipping {resource} {i}.')
                    continue
        shutil.rmtree(work_dir, ignore_errors=True)
        Path.mkdir(work_dir, parents=True, exist_ok=True)
        out = open(out_file, 'w')
        err = open(work_dir / 'err.txt', 'w')
        Pcheck()
        p = Popen([gem5, cwd / 'test.py', '--resource', resource,
                   '--width', width, '--freq', freq,
                   '--l1dsize', l1dsize, '--l1dassoc', l1dassoc, '--l1dmshr', l1dmshr,
                   '--l1isize', l1isize, '--l1iassoc', l1iassoc, '--l1imshr', l1imshr,
                   '--l2size', l2size, '--l2assoc', l2assoc, '--l2mshr', l2mshr, '--l2policy', l2policy,
                   '--cache_line', cache_line],
                   cwd=work_dir, stdout=out, stderr=err)
        sub_proc.append((p, out, err))

for p, out, err in sub_proc:
    ret = p.wait()
    out.close()
    err.close()
    if ret != 0:
        print(f'Error exit code {ret} from subprocess {p.args}.')

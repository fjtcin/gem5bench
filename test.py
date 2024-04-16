import argparse

from armv7a import O3_ARM_v7a_3
from cache import CacheHierarchy
from gem5.components.boards.simple_board import SimpleBoard
from gem5.components.memory.memory import ChanneledMemory
from gem5.components.memory.dram_interfaces.ddr3 import DDR3_1600_8x8
from gem5.components.processors.base_cpu_core import BaseCPUCore
from gem5.components.processors.base_cpu_processor import BaseCPUProcessor
from gem5.isas import get_isa_from_str
from gem5.resources.resource import obtain_resource
from gem5.simulate.simulator import Simulator

from m5.core import setInterpDir
setInterpDir('/home/fjtcin/Documents/arm/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-linux-gnu/aarch64-none-linux-gnu/libc')

parser = argparse.ArgumentParser(description="A gem5 script for running simple binaries in SE mode.")
parser.add_argument("--resource", type=str, default='arm-hello64-static', help="The gem5 resource binary to run.")
parser.add_argument('--width', type=int, default=8, help='The issue width.')
parser.add_argument('--freq', type=str, default='1GHz', help='The CPU clock frequency.')

parser.add_argument('--l1dsize', type=str, default='32KiB', help='Size of the L1 data cache.')
parser.add_argument('--l1dassoc', type=int, default=2, help='Associativity of the L1 data cache.')
parser.add_argument('--l1dmshr', type=int, default=6, help='Number of MSHRs in the L1 data cache.')

parser.add_argument('--l1isize', type=str, default='32KiB', help='Size of the L1 instruction cache.')
parser.add_argument('--l1iassoc', type=int, default=2, help='Associativity of the L1 instruction cache.')
parser.add_argument('--l1imshr', type=int, default=2, help='Number of MSHRs in the L1 instruction cache.')

parser.add_argument('--l2size', type=str, default='1MiB', help='Size of the L2 cache')
parser.add_argument('--l2assoc', type=int, default=16, help='Associativity of the L2 cache.')
parser.add_argument('--l2mshr', type=int, default=16, help='Number of MSHRs in the L2 cache.')
parser.add_argument('--l2policy', type=str, default='Random', help='The replacement policy of the L2 cache.')

parser.add_argument('--cache_line', type=int, default=64, help='The cache line size.')
args = parser.parse_args()

# Setup the system.
memory = ChanneledMemory(DDR3_1600_8x8, 1, args.cache_line)  # SingleChannelDDR3_1600()

cache_hierarchy = CacheHierarchy(
    l1d_size=args.l1dsize,
    l1d_assoc=args.l1dassoc,
    l1d_mshrs=args.l1dmshr,
    l1i_size=args.l1isize,
    l1i_assoc=args.l1iassoc,
    l1i_mshrs=args.l1imshr,
    l2_size=args.l2size,
    l2_assoc=args.l2assoc,
    l2_mshrs=args.l2mshr,
    l2_policy=args.l2policy,
)

O3_ARM_v7a_3.update(args.width)
core = O3_ARM_v7a_3()
cores = [
    BaseCPUCore(
        core=core,
        isa=get_isa_from_str('arm'),
    )
]
processor = BaseCPUProcessor(
    cores=cores,
)

motherboard = SimpleBoard(
    clk_freq=args.freq,
    processor=processor,
    memory=memory,
    cache_hierarchy=cache_hierarchy,
)
motherboard.cache_line_size = args.cache_line

from m5.objects import RedirectPath
motherboard.redirect_paths = [RedirectPath(app_path='/lib64', host_paths=['/home/fjtcin/Documents/arm/arm-gnu-toolchain-13.2.Rel1-x86_64-aarch64-none-linux-gnu/aarch64-none-linux-gnu/libc/lib64', '/home/fjtcin/Documents/prep/benchmark/mibench/office/rsynth/gdbm/usr/lib'])]

# Set the workload
binary = obtain_resource(args.resource)
motherboard.set_workload(binary)

# Run the simulation
simulator = Simulator(board=motherboard)
simulator.run()

print(
    "Exiting @ tick {} because {}.".format(
        simulator.get_current_tick(), simulator.get_last_exit_event_cause()
    )
)

from armv7a import (
    O3_ARM_v7a_ICache,
    O3_ARM_v7a_DCache,
    O3_ARM_v7aL2,
)
from m5.objects import (
    L2XBar,
    SystemXBar,
    BadAddr,
)
from gem5.components.cachehierarchies.classic.abstract_classic_cache_hierarchy import AbstractClassicCacheHierarchy
from gem5.components.cachehierarchies.classic.caches.mmu_cache import MMUCache


class CacheHierarchy(AbstractClassicCacheHierarchy):
    def __init__(self, l1d_size, l1d_assoc, l1d_mshrs, l1i_size, l1i_assoc, l1i_mshrs, l2_size, l2_assoc, l2_mshrs, l2_policy):
        super().__init__()
        O3_ARM_v7a_ICache.update(l1i_size, l1i_mshrs, l1i_assoc)
        O3_ARM_v7a_DCache.update(l1d_size, l1d_mshrs, l1d_assoc)
        O3_ARM_v7aL2.update(l2_size, l2_mshrs, l2_assoc, l2_policy)
        membus = SystemXBar(width=64)
        membus.badaddr_responder = BadAddr()
        membus.default = membus.badaddr_responder.pio
        self.membus = membus

    def get_mem_side_port(self):
        return self.membus.mem_side_ports

    def get_cpu_side_port(self):
        return self.membus.cpu_side_ports

    def incorporate_cache(self, board):
        # Set up the system port for functional access from the simulator.
        board.connect_system_port(self.membus.cpu_side_ports)

        for _, port in board.get_memory().get_mem_ports():
            self.membus.mem_side_ports = port

        self.l1icaches = [
            O3_ARM_v7a_ICache()
            for _ in range(board.get_processor().get_num_cores())
        ]
        self.l1dcaches = [
            O3_ARM_v7a_DCache()
            for _ in range(board.get_processor().get_num_cores())
        ]
        self.l2buses = [
            L2XBar() for _ in range(board.get_processor().get_num_cores())
        ]
        self.l2caches = [
            O3_ARM_v7aL2()
            for _ in range(board.get_processor().get_num_cores())
        ]
        # ITLB Page walk caches
        self.iptw_caches = [
            MMUCache(size="8KiB")
            for _ in range(board.get_processor().get_num_cores())
        ]
        # DTLB Page walk caches
        self.dptw_caches = [
            MMUCache(size="8KiB")
            for _ in range(board.get_processor().get_num_cores())
        ]

        for i, cpu in enumerate(board.get_processor().get_cores()):
            cpu.connect_icache(self.l1icaches[i].cpu_side)
            cpu.connect_dcache(self.l1dcaches[i].cpu_side)

            self.l1icaches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.l1dcaches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.iptw_caches[i].mem_side = self.l2buses[i].cpu_side_ports
            self.dptw_caches[i].mem_side = self.l2buses[i].cpu_side_ports

            self.l2buses[i].mem_side_ports = self.l2caches[i].cpu_side

            self.membus.cpu_side_ports = self.l2caches[i].mem_side

            cpu.connect_walker_ports(
                self.iptw_caches[i].cpu_side, self.dptw_caches[i].cpu_side
            )

            cpu.connect_interrupt()

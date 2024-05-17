# gem5bench

This project is an example to automate benchmarking using gem5 stdlib. We benchmarked [O3_ARM_v7a](https://github.com/gem5/gem5/blob/stable/configs/common/cores/arm/O3_ARM_v7a.py) with the [MediaBench](https://cs.slu.edu/~fritts/mediabench/mb1/index.html) and [MiBench](https://vhosts.eecs.umich.edu/mibench/). The result can be found at [gem5bench-result](https://github.com/fjtcin/gem5bench-result).

## Running

To run the benchmark, you need to modify some paths in `main.py`, `test.py`, and three json config files. These paths specify the locations of gem5, aarch64 glibc, and the benchmark suites.

You need also to make some modifications to the gem5 source code:

```python
# se_binary_workload.py, change the formal parameters of function set_se_binary_workload
cwd: Optional[str] = None,
stdin_file: Optional[str] = None,
stdout_file: Optional[str] = None,
stderr_file: Optional[str] = None,

# se_binary_workload.py, in function set_se_binary_workload
if cwd is not None:
    process.cwd = cwd
if stdin_file is not None:
    process.input = stdin_file
if stdout_file is not None:
    process.output = stdout_file
if stderr_file is not None:
    process.errout = stderr_file
```

```c++
// se_workload.cc, implement these system calls in class SyscallTable64
{   base + 88, "utimensat", ignoreFunc },
{  base + 435, "clone3", clone3Func<ArmLinux64> },
```

```c++
// linux.hh, define the following struct in class ArmLinux64
struct tgt_clone_args
{
    uint64_t flags;
    uint64_t pidfd;
    uint64_t child_tid;
    uint64_t parent_tid;
    uint64_t exit_signal;
    uint64_t stack;
    uint64_t stack_size;
    uint64_t tls;
    uint64_t set_tid;
    uint64_t set_tid_size;
    uint64_t cgroup;
};
```

After making these necessary changes, you can run the command below. It will create a directory `output`, which includes all simulation results. By default, 32 gem5 tasks will be running in parallel. You can change this with the `-j` option.

```bash
python main.py -j32
```

> Version of our gem5 (git hash):
>
> ee6f1377d7c54422137dfa47cd4d73407814867d

## Notes on compiling

We have compiled most benchmark tasks to the aarch64 format binaries successfully. You can find the source codes and corresponding binaries in the `benchmark` directory. We have changed some Makefiles and even source codes, otherwise there will be errors when compiling. These changes are made only to resolve compilation errors, and they do not change any behavior of the programs. The compressed tarballs contain all the original source codes.

> Version of our compiler:
>
> aarch64-none-linux-gnu-gcc (Arm GNU Toolchain 13.2.rel1 (Build arm-13.7)) 13.2.1 20231009

### Failed benchmark programs

Currently, there are still some benchmark programs we failed to run successfuly. If you have any idea, feel free to contribute.

### mediabench/pegwit

The program can be compiled successfully, but when running, it will cause errors:

```text
*** stack smashing detected ***: terminated
Aborted (core dumped)
```

and

```text
Bus error (core dumped)
```

### mediabench/pgp and mibench/security/pgp

The program can be compiled successfully, but when running, it will cause errors:

```text
Segmentation fault (core dumped)
```

### mediabench/rasta

We failed to compile this program. The program relies on the SPHERE C-language library, but we cannot get the linking object required (-lsp) for the aarch64 architecture. [It is said](https://stackoverflow.com/questions/16394518/nist-sphere-format-files) that `sphere_2.6a.tar` is not supported on modern systems.

### mibench/consumer/tiff

The program can be compiled successfully, but when running, it will cause errors:

```text
Seek error accessing TIFF directory.
```

### mibench/office/ispell

The program can be compiled successfully, but when running, it will cause errors:

```text
Illegal format hash table
```

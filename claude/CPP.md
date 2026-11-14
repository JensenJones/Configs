# C++ for low-latency trading

Defaults for when the codebase does not already decide. The codebase always wins: its C++ standard, containers, allocators, error handling and style come first.

## Know which path you are on

Before changing code, work out whether it runs on the hot path (per market-data tick or per order) or the cold path (startup, configuration, recovery, tooling). Ask if it is unclear.

- Cold path: write for clarity and correctness. Do not optimise it.
- Hot path: the rules below apply, and every change needs a stated latency effect and a measurement.

## Hot path

- No allocation. No `new`, `malloc`, growing `std::string` or `std::vector`, `std::function`, `std::shared_ptr` copies, or node containers (`std::map`, `std::list`, `std::unordered_map`). Preallocate at startup; use fixed-capacity containers, pools and flat or open-addressing tables.
- No system calls, locks, blocking I/O or string formatting. Hand logging and I/O to another thread through a preallocated queue.
- No exceptions thrown. Report expected failures by value (`std::expected`, an error code, `std::optional`). Exceptions are for unrecoverable cold-path errors, if the codebase uses them at all.
- Prefer static dispatch (templates, CRTP, `std::variant`) to virtual calls where the type is known at compile time.
- Keep data contiguous and small. Arrays of values over pointers to nodes; split rarely used fields away from hot ones; order members to avoid padding; use the narrowest type that fits.
- Keep the common case branch-free or predictable. Put the rare case out of line. Add `[[likely]]`, `[[unlikely]]` or forced inlining only when a measurement supports it.
- Share nothing between threads if you can. Where you must, use single-producer single-consumer ring buffers, and give each thread's writable state its own cache line (`alignas(std::hardware_destructive_interference_size)`) to prevent false sharing.
- Do the work early: compute at compile time (`constexpr`, lookup tables) or at startup, not per message.
- Prices and quantities are integers in fixed-point ticks or strong types, never floating point compared for equality.
- Pass small trivially copyable types by value, everything else by `const&`, `std::span` or `std::string_view`. Do not copy on the hot path.

## Measure

- Never claim something is faster without a number. State what you measured, how, and on what build.
- Benchmark only optimised builds with the production flags. A Debug build can reverse which option wins.
- Report the tail (p99, p99.9, max) as well as the median. In trading the slow outlier matters more than the mean.
- Microbenchmarks: use the repo's harness or Google Benchmark, stop the compiler deleting the work (`DoNotOptimize`), use realistic data and sizes, and compare before and after on the same quiet machine.
- For a hot loop, read the generated assembly, and use hardware counters (`perf stat`: cache misses, branch misses, instructions per cycle) to explain the result.
- If you cannot measure it here, say so and describe the benchmark I should run.

## Correctness

- Undefined behaviour is a bug even when it appears to work. Keep code clean under `-Wall -Wextra` and the repo's warning set, and run tests under AddressSanitizer, UndefinedBehaviorSanitizer and ThreadSanitizer where the build supports them.
- RAII for every resource. Rule of zero where possible; otherwise define or delete all five special members. Mark move operations `noexcept`.
- No raw owning pointers. No C-style casts. No signed and unsigned mixed in comparisons or arithmetic.
- `const` and `constexpr` by default. `explicit` on single-argument constructors. `[[nodiscard]]` on functions whose result must be checked. `enum class` over plain enums.
- Use strong types for prices, quantities, identifiers and timestamps so they cannot be swapped.
- Every shared mutable variable needs an obvious owner or synchronisation. State the memory order you chose for an atomic and why.
- Avoid macros. No `using namespace` in headers. Include only what the file uses, and forward declare where that keeps headers light.

## Tests

- Add or update tests with every behaviour change, in the repo's framework.
- Tests are deterministic: no wall-clock time, fixed random seeds, no dependence on thread timing.
- Cover the edges trading code breaks on: empty book, crossed book, zero and maximum quantity, integer overflow, sequence gaps, out-of-order and duplicate messages.

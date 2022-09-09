# Search Speed Test
Comparison of execution times for searches on numeric vs tag vs text fields for a simple single value scenario.
## Usage
### Single Key Value, synchronous
```bash
python3 test.py
Average num search execution time: 123089.675 ns
Average tag search execution time: 122802.905 ns
Average txt search execution time: 124719.211 ns
```
### Multiple Key values, asynchronous
```bash
python3 async_test.py
Average num search execution time: 167124.96 ns
Average tag search execution time: 164783.553 ns
Average txt search execution time: 166314.065 ns
```
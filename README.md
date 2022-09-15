# Search Speed Test
Comparison of execution times for searches on numeric vs tag vs text fields for a simple single value scenario.
## Usage
### Single Key Value, synchronous
```bash
python3 test.py
Average num search execution time: 135799.646 ns
Average tag search execution time: 124620.042 ns
Average txt search execution time: 126496.432 ns
```
### Multiple Key values, asynchronous
```bash
python3 async_test.py
Average num search execution time: 185705.49 ns
Average tag search execution time: 174767.251 ns
Average txt search execution time: 176455.705 ns
```
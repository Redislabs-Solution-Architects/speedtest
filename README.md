# Search Speed Test
Comparison of execution times for searches on numeric vs tag vs text fields for a simple single value scenario.
## Usage
### 100,000 Keys per Index, synchronous
```bash
python3 test.py 100000
Average num search execution time: 163231.184 ns
Average tag search execution time: 123353.831 ns
Average txt search execution time: 123796.847 ns
```

# Search Speed Test
Comparison of execution times for searches on numeric vs tag vs text fields for a simple single value scenario.
## Usage
### Options
- --url. Redis connection string.  Default = redis://localhost:6379
- --nkeys. Number of keys to be generated each field type (tag, text, numeric).  Default = 1,000,000.
- --iterations. Number of test iterations (searches) Default = 100,000.
### Execution
```bash
python3 numeric-search-test.py
```
### Output
Num keys:1000000, Test iterations:100000
|          |   Numeric |      Tag |     Text |
|:---------|----------:|---------:|---------:|
| Ave (ms) |  0.348216 | 0.316053 | 0.320673 |
| 10% (ms) |  0.248493 | 0.216333 | 0.22074  |
| 50% (ms) |  0.339097 | 0.309557 | 0.311574 |
| 90% (ms) |  0.45274  | 0.411892 | 0.420228 |

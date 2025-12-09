# 🏛 Quorum Coding Challenge

This repository processes legislative voting records and produces two summary outputs:

| File | Description |
|------|-------------|
| `output/legislators-support-oppose-count.csv` | Number of bills each legislator supported or opposed |
| `output/bills.csv` | Number of supporters/opposers for each bill + sponsor name |


---

## 🔧 Requirements

- Python 3.13
- pandas
- pytest
- pytest-cov

Install dependencies:

```
pip install pandas pytest pytest-cov
```
▶ How to Run
```
python main.py
```

▶ How to Test
```
pytest -q
```

▶ How to Test with coverage
```
pytest --cov=.
```

### 1. Time complexity & tradeoffs

My solution uses vectorized pandas operations — filtering, grouping, mapping, joining, and writing to CSV. Under the hood these still iterate over rows in memory, so both time and space complexity are **O(n)**.

Tradeoffs:

- Chose Pandas instead of raw Python loops/dicts — keeps the code shorter, more expressive, and takes advantage of vectorized operations
- Loading the entire dataset into memory keeps the implementation simple and easy to reason about
- Suitable for what I expect to be typical legislative-scale data (thousands to low millions). If the dataset grew beyond in-memory capacity, I’d consider chunked Pandas processing, Dask for larger-than-RAM workloads, loading into a SQL database for pushdown execution, or Spark for distributed processing — depending on data size, query patterns, and available infrastructure


### 2. How would you change your solution to account for future columns that might be requested, such as “Bill Voted On Date” or “Co-Sponsors”?

The code already merges/matches relationally, so new fields can be added easily.

- Bill Voted On Date: Add a vote_date column into the merged DataFrame and include it in aggregations
- Co-Sponsors: Map directly for listing, or explode() only when per-sponsor analysis (counting/joining/aggregation) is needed

### 3. How would you change your solution if instead of receiving CSVs of data, you were given a list of legislators or bills that you should generate a CSV for?
   
I would convert them into DataFrames and reuse the same logic without algorithmic changes. Alternatively, a pure Python dictionary implementation could replace pandas for stream-oriented or very large data.


### 4. How long did you spend working on the assignment?
About 4 hours — slightly above the suggested window because I needed to re-familiarize myself with Pandas while writing the solution, wrote several tests to verify correctness and coverage, and polished the README.
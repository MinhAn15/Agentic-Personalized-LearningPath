# VLOOKUP (Vertical Lookup)

## Definition
VLOOKUP is an Excel function used to search for a specific value in the first column of a table array and return a value in the same row from another column. It stands for "Vertical Lookup".

## Syntax
`=VLOOKUP(lookup_value, table_array, col_index_num, [range_lookup])`

- **lookup_value**: The value you want to search for.
- **table_array**: The range of cells containing the data. The first column involving the range must contain the `lookup_value`.
- **col_index_num**: The column number in the `table_array` from which to retrieve the value. The first column is 1.
- **range_lookup**: Optional. `TRUE` (approximate match) or `FALSE` (exact match). Default is `TRUE`.

## Example
Imagine a table of products:
| A | B | C |
|---|---|---|
| ID | Product | Price |
| 101 | Apple | $1.00 |
| 102 | Banana | $0.50 |

To find the price of "Banana" (ID 102):
`=VLOOKUP(102, A2:C3, 3, FALSE)` returns `$0.50`.

## Common Pitfalls
1.  **First Column Rule**: The `lookup_value` MUST be in the first column of the `table_array`.
2.  **Approximate Match**: Forgetting `FALSE` can lead to wrong results if the data isn't sorted.
3.  **Static References**: When copying formula, ensure `table_array` uses absolute references (e.g., `$A$2:$C$10`).

## Real-World Use Case
Merging data from two different sheets based on a common identifier (e.g., adding "Department Name" to an "Employee List" using "Dept ID").

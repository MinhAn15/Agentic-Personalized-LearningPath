
# SQL Basics: SELECT, FROM, WHERE

## Learning Objectives
By the end of this module, you will be able to:
- Write basic SQL SELECT statements
- Filter data using WHERE clauses
- Understand data types in SQL

## 1. Introduction to SQL
SQL (Structured Query Language) is the standard language for interacting with relational databases.

### Key Concepts
- **Tables**: Data is stored in tables with rows and columns
- **Columns**: Each column has a specific data type (INT, VARCHAR, DATE, etc.)
- **Rows**: Each row represents a single record

## 2. The SELECT Statement
```sql
SELECT column1, column2
FROM table_name;
```

### Example
```sql
SELECT first_name, last_name, email
FROM employees;
```

## 3. The WHERE Clause
```sql
SELECT column1, column2
FROM table_name
WHERE condition;
```

### Comparison Operators
| Operator | Description |
|----------|-------------|
| = | Equal |
| <> | Not equal |
| > | Greater than |
| < | Less than |
| >= | Greater than or equal |
| <= | Less than or equal |

## Practice Exercises
1. Write a query to select all columns from the `customers` table
2. Write a query to select customers where `country = 'Vietnam'`
3. Write a query to select products with `price > 100`

## Summary
- SELECT retrieves data from tables
- FROM specifies the table
- WHERE filters the results

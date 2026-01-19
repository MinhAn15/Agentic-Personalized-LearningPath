
# SQL JOINs: INNER, LEFT, RIGHT, FULL

## Learning Objectives
- Understand the concept of table relationships
- Write INNER JOIN queries
- Differentiate between LEFT, RIGHT, and FULL JOINs

## 1. Why JOINs?
In relational databases, data is often split across multiple tables. JOINs allow us to combine related data.

## 2. INNER JOIN
Returns only rows with matching values in both tables.

```sql
SELECT orders.order_id, customers.customer_name
FROM orders
INNER JOIN customers ON orders.customer_id = customers.id;
```

## 3. LEFT JOIN
Returns all rows from the left table, and matching rows from the right table.

```sql
SELECT customers.customer_name, orders.order_id
FROM customers
LEFT JOIN orders ON customers.id = orders.customer_id;
```

## 4. RIGHT JOIN
Returns all rows from the right table, and matching rows from the left table.

## 5. FULL OUTER JOIN
Returns all rows when there is a match in either table.

## Practice Exercises
1. Write an INNER JOIN between `employees` and `departments`
2. Write a LEFT JOIN to find all customers, including those without orders
3. Explain when you would use a RIGHT JOIN vs LEFT JOIN

## Summary
- JOINs combine data from multiple tables
- INNER JOIN: Only matching rows
- LEFT/RIGHT JOIN: All rows from one side, matching from other
- FULL JOIN: All rows from both sides

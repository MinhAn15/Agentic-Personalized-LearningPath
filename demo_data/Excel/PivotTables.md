# PivotTables

## Definition
A PivotTable is a powerful tool to calculate, summarize, and analyze data that lets you see comparisons, patterns, and trends in your data. It works by reorganizing "raw" data into a summarized format without changing the original dataset.

## Core Areas
1.  **Rows**: The fields you want to list down the left side (e.g., "Product Category").
2.  **Columns**: The fields you want to expand across the top (e.g., "Year" or "Region").
3.  **Values**: The data you want to calculate (e.g., Sum of "Sales" or Count of "Orders").
4.  **Filters**: Fields used to restrict the data shown in the PivotTable (e.g., filter by "Salesperson").

## Example
**Scenario**: You have 10,000 rows of sales data containing Date, Product, Region, and Amount.
**Goal**: Find total sales per Region.

**Steps**:
1.  Select Data > Insert > PivotTable.
2.  Drag "Region" to **Rows**.
3.  Drag "Amount" to **Values**.
**Result**: A small table showing the Sum of Amount for East, West, North, South.

## Slicers
Slicers are visual filters. Instead of using the drop-down in the PivotTable header, a Slicer provides buttons that you can click to filter the data, making dashboards interactive.

## Calculated Fields
You can add your own formulas inside a PivotTable. For example, creating a "Tax" field that is `Amount * 0.10`, even if "Tax" doesn't exist in the source data.

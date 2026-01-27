# Data Validation

## Definition
Data Validation is a feature that controls what can be entered into a cell. It is crucial for maintaining data integrity, especially when multiple users edit a spreadsheet.

## Common Types
1.  **List**: restricts input to a predefined set of items (creates a dropdown menu).
2.  **Whole Number**: restricts input to integers between a min and max (e.g., Age 18-100).
3.  **Date**: restricts input to valid dates within a range.
4.  **Custom Formula**: uses a logical formula to validate input (e.g., ensure cell A1 is not equal to cell B1).

## Example: Creating a Dropdown List
**Goal**: Ensure users only select "HR", "IT", or "Sales" for the Department column.

**Steps**:
1.  Select the cells to validate.
2.  Go to **Data** tab > **Data Validation**.
3.  Under **Allow**, select **List**.
4.  In **Source**, type: `HR, IT, Sales`.
5.  Click OK.
**Result**: A dropdown arrow appears in the cell with those options.

## Input Messages & Error Alerts
-   **Input Message**: A yellow tooltip that appears when a user clicks the cell (e.g., "Please select a department").
-   **Error Alert**: A popup that blocks invalid data (Stop) or warns the user (Warning) if they try to type "Finance" when it's not in the list.

## Circle Invalid Data
If validation is applied *after* data entry, you can use "Circle Invalid Data" to highlight cells that violate the new rules.

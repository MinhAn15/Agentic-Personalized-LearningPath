# Macros & VBA

## Definition
A **Macro** is an action or a set of actions that you can run as many times as you want. When you create a macro, you are recording your mouse clicks and keystrokes.
**VBA (Visual Basic for Applications)** is the programming language used to write macros.

## Recording vs. Writing
-   **Recording**: Excel watches what you do (e.g., formatting a header blue and bold) and writes the VBA code for you. It is limited to exact repetition.
-   **Writing**: You write custom logic (Loops, If/Then statements) in the VBA Editor for complex automation.

## Example: A Simple "Format" Macro
**Scenario**: You always receive a raw report that needs formatting.
**Steps**:
1.  Developer Tab > Record Macro.
2.  Name it "FormatReport".
3.  Perform actions: Bold header, AutoFit columns, Add borders.
4.  Stop Recording.
**Usage**: Next time, just click the "FormatReport" button (or shortcut `Ctrl+Shift+F`) to apply all steps instantly.

## Security (macro-enabled workbooks)
Because Macros can contain malicious code, Excel does not save them in standard `.xlsx` files. You must save macro-containing files as **Excel Macro-Enabled Workbook (.xlsm)**.

## Relative vs. Absolute References
-   **Absolute (Default)**: If you record clicking cell A1, the macro will *always* go to A1.
-   **Relative**: If you toggle "Use Relative References" on, the macro performs the action *relative* to the active cell (e.g., "move one cell right").

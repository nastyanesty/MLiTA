# Neuro-Symbolic Logical Problem Solver

## Resolution Algorithm - res.py

### Input

The algorithm takes as input disjunctions of literals, also known as clauses or resolvents. It supports negation and any number of arguments.

### Algorithm Description

The process is as follows:
1. Generate Resolvents: The algorithm generates all possible resolvents using the most recently added clause. It prioritizes creating shorter resolvents and resolvents containing constants.
2. Update Active Clauses: These newly generated resolvents are added to the active_clauses list.
3. Iterate: Steps 1 and 2 are repeated for the new clauses in active_clauses.

Termination Condition: The process continues until an "empty" resolvent (a contradiction) is found, indicating that the initial set of clauses is unsatisfiable.

## Examples - main.py, test.py

Basic resolvents created from a text of problem using LLM

## Parsing - helper.py

Preparing basic resolvents for input

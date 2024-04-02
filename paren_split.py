import sys
import re

def paren_split(string: str) -> list:
    """Splits a string into sub a list of subarrays and strings
    based on parentheses nesting
    
    Example:
    - 'test': ['test']
    - 'test (test1)': [['test', ['test1']]]
    - 'test (test1), test2': [['test', ['test1']], 'test2']
    """

    res = []
    paren_stack = []

    string = string.strip()

    try:
        while len(string) > 0:
            # Get indices of important elements
            comma_index = re.search(",|;", string)
            open_brace_index = re.search("\[|{|\(", string)
            close_brace_index = re.search("\]|}|\)", string)

            comma_index = comma_index.start() if comma_index else -1
            open_brace_index = open_brace_index.start() if open_brace_index else -1
            close_brace_index = close_brace_index.start() if close_brace_index else -1

            # Reach into the deepest layer based on the parantheses stack
            depth = len(paren_stack)
            if(depth > 0):
                depth += 1
            curr = res
            while depth > 0:
                depth -= 2
                curr = curr[len(curr) - 1]
                curr = curr[len(curr) - 1]

            # Deal with leading commas or close braces in string
            if comma_index == 0 or close_brace_index == 0:
                string = string[1:].strip()
            elif close_brace_index == 0:
                string = string[1:].strip()
                paren_stack.pop()
            # Append everything else if no more braces
            elif open_brace_index <= -1 and len(paren_stack) <= 0:
                for str in re.split(",|;", string):
                    curr.append(str.strip())
                break
            # Add element to stack if open brace hit
            elif (open_brace_index >= 0 and open_brace_index < comma_index) or (open_brace_index >= 0 and comma_index <= -1):
                paren_stack.append(string[open_brace_index])
                curr.append([string[0:open_brace_index].strip(),[]])
                string = string[(open_brace_index+1):].strip()
            # Place elements into their respective place
            else:
                if comma_index == -1 or close_brace_index < comma_index:
                    curr.append(string[0:close_brace_index])
                    string = string[(close_brace_index+1):].strip()
                    paren_stack.pop()
                else:
                    curr.append(string[0:comma_index].strip())
                    string = string[(comma_index+1):].strip()
    except:
        raise Exception(
            "Encountered an error while parsing an in item's ingredient list. Ensure all parentheses are balanced: " + string
        )

    return res
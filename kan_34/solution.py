from typing import List, Union

def count_elements_greater_than_previous_average(arr: List[Union[int, float]]) -> int:
    """
    Calculate the frequency of elements that exceed the arithmetic mean of all preceding elements.

    Args:
        arr (List[Union[int, float]]): A list of numerical values.

    Returns:
        int: Count of elements exceeding the preceding average.

    Raises:
        TypeError: If the input is not a list.
        ValueError: If any element in the list is not a number.
    """
    if not isinstance(arr, list):
        raise TypeError("Input must be a list.")
        
    if not arr or len(arr) == 1:
        return 0

    count = 0
    current_sum = arr[0]
    
    if not isinstance(current_sum, (int, float)):
        raise ValueError("All elements in the list must be numbers.")

    for i in range(1, len(arr)):
        if not isinstance(arr[i], (int, float)):
            raise ValueError("All elements in the list must be numbers.")
            
        previous_average = current_sum / i
        if arr[i] > previous_average:
            count += 1
            
        current_sum += arr[i]

    return count

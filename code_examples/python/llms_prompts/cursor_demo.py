# Let's do the fibonacci sequence

def fibonacci(n):
    """
    Generate Fibonacci sequence up to n numbers
    Args:
        n (int): Number of Fibonacci numbers to generate
    Returns:
        list: List containing n Fibonacci numbers
    """
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    
    sequence = [0, 1]
    while len(sequence) < n:
        sequence.append(sequence[-1] + sequence[-2])
    
    return sequence

def main():
    # Get user input for the number of Fibonacci numbers
    n = int(input("Enter how many Fibonacci numbers to generate: "))
    
    # Generate and print the sequence
    result = fibonacci(n)
    print(f"The first {n} numbers in the Fibonacci sequence are:")
    print(result)

if __name__ == "__main__":
    main()

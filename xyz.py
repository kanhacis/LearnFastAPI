## Factorial of a number
def fact(n):
    if n == 1:
        return 1
    
    return n * fact(n-1)

# print(fact(2))


## Print one to n
def one_to_n(n):
    if n == 0:
        return 0
    
    one_to_n(n-1)
    print(n)
    
# one_to_n(10)


## Print n to one
def n_to_one(n):
    if n == 0:
        return 0
    
    print(n)
    return n_to_one(n-1)
    
# n_to_one(10)


 # Python code to implement Fibonacci series

# Function for fibonacci
def fib(n):

    # Stop condition
    if (n == 0):
        return 0

    # Stop condition
    if (n == 1 or n == 2):
        return 1

    # Recursion function
    else:
        return (fib(n - 1) + fib(n - 2))


# Initialize variable n.
n = 5

print("Fibonacci series of 5 numbers is :",end=" ")

print(fib(n)) 


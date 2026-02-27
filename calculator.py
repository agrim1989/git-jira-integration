class Calculator:
    """A simple calculator class to perform basic arithmetic operations."""

    def add(self, a: float, b: float) -> float:
        return a + b

    def subtract(self, a: float, b: float) -> float:
        return a - b

    def multiply(self, a: float, b: float) -> float:
        return a * b

    def divide(self, a: float, b: float) -> float:
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b


def main():
    calc = Calculator()
    print("--- Simple CLI Calculator ---")
    print("Operations: +, -, *, / (or 'exit' to quit)")

    while True:
        try:
            choice = input("\nEnter operation (+, -, *, /) or 'exit': ").strip().lower()
            if choice == 'exit':
                break

            if choice not in ['+', '-', '*', '/']:
                print("Invalid operator. Please try again.")
                continue

            num1 = float(input("Enter first number: "))
            num2 = float(input("Enter second number: "))

            if choice == '+':
                print(f"Result: {calc.add(num1, num2)}")
            elif choice == '-':
                print(f"Result: {calc.subtract(num1, num2)}")
            elif choice == '*':
                print(f"Result: {calc.multiply(num1, num2)}")
            elif choice == '/':
                print(f"Result: {calc.divide(num1, num2)}")

        except ValueError as e:
            print(f"Error: {e}")
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()

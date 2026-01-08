import re
import math

class Calculator:
    def __init__(self):
        self.operations = {
            'plus': '+',
            'add': '+',
            'minus': '-',
            'subtract': '-',
            'times': '*',
            'multiply': '*',
            'multiplied by': '*',
            'divide': '/',
            'divided by': '/',
            'power': '**',
            'to the power': '**',
            'square root': 'sqrt',
            'sqrt': 'sqrt'
        }

    def parse_math_expression(self, text):
        """Parse spoken math expression into evaluable form"""
        # Convert spoken words to symbols
        expr = text.lower()

        for word, symbol in self.operations.items():
            expr = expr.replace(word, symbol)

        # Handle square root specially
        if 'sqrt' in expr:
            # Find numbers after sqrt
            sqrt_match = re.search(r'sqrt\s+(\d+(?:\.\d+)?)', expr)
            if sqrt_match:
                number = float(sqrt_match.group(1))
                result = math.sqrt(number)
                return f"The square root of {number} is {result:.2f}"

        # Clean up the expression for evaluation
        expr = re.sub(r'[^\d+\-*/().\s]', '', expr)  # Keep only numbers and operators

        try:
            # Safely evaluate the expression
            result = eval(expr, {"__builtins__": {}}, {})
            return f"The result is {result}"
        except (SyntaxError, NameError, ZeroDivisionError) as e:
            return f"Sorry, I couldn't calculate that. Error: {str(e)}"

    def calculate(self, expression):
        """Main calculation function"""
        return self.parse_math_expression(expression)

def calculate_expression(text):
    """Simple wrapper function for calculation"""
    calc = Calculator()
    return calc.calculate(text)

if __name__ == "__main__":
    # Test the calculator
    print(calculate_expression("5 plus 3"))
    print(calculate_expression("10 divided by 2"))
    print(calculate_expression("square root of 16"))

"""
Banking System Error Handling Framework
Version 1.0

This module demonstrates three major types of errors and their handling techniques:
1. Syntax Errors - Caught and handled during input parsing
2. Runtime Exceptions - Using try-except blocks
3. Logical Errors - Using assertions and validation
"""

import re
from decimal import Decimal, InvalidOperation

# Custom Exception Hierarchy
class BankingException(Exception):
    """Base exception class for all banking-related exceptions."""
    def __init__(self, message, error_code=None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

# Validation Exceptions (for handling syntax errors)
class InvalidInputError(BankingException):
    """Exception raised for invalid input formats or values."""
    pass

class InvalidAmountError(InvalidInputError):
    """Exception raised when transaction amount is invalid (negative or zero)."""
    def __init__(self, amount):
        super().__init__(f"Invalid amount: {amount}. Amount must be positive.", "E001")

# Transaction Exceptions (for handling runtime errors)
class InsufficientFundsError(BankingException):
    """Exception raised when account has insufficient funds for withdrawal."""
    def __init__(self, account_id, amount, balance):
        super().__init__(
            f"Insufficient funds in account {account_id}. "
            f"Attempted to withdraw {amount}, but balance is {balance}.", 
            "T001"
        )

class InputValidator:
    """Handles validation of user inputs to catch syntax errors early."""
    
    @staticmethod
    def validate_amount(amount):
        """
        Validates that an amount is a positive decimal number.
        
        Args:
            amount: The amount to validate (string or number)
            
        Returns:
            Decimal: The validated amount as a Decimal
            
        Raises:
            InvalidAmountError: If amount is negative or zero
            InvalidInputError: If amount cannot be converted to Decimal
        """
        try:
            # Syntax error handling: Convert string to Decimal
            amount_decimal = Decimal(str(amount))
            
            # Logical error prevention: Check if amount is positive
            if amount_decimal <= Decimal('0'):
                raise InvalidAmountError(amount)
                
            return amount_decimal
            
        except InvalidOperation:
            # Syntax error: Input wasn't a valid number
            raise InvalidInputError(
                f"Invalid amount format: '{amount}'. Must be a valid number.", 
                "E003"
            ) from None

    @staticmethod
    def validate_account_id(account_id):
        """
        Validates account ID format to catch syntax errors.
        
        Args:
            account_id: The account ID to validate
            
        Returns:
            str: The validated account ID
            
        Raises:
            InvalidInputError: If account_id format is invalid
        """
        # Example: require alphanumeric ID with 8-12 characters
        if not isinstance(account_id, str):
            raise InvalidInputError("Account ID must be a string", "E004")
            
        if not re.match(r'^[a-zA-Z0-9]{8,12}$', account_id):
            raise InvalidInputError(
                f"Invalid account ID format: '{account_id}'. "
                f"Must be 8-12 alphanumeric characters.", 
                "E005"
            )
            
        return account_id

class BankAccount:
    """Simple bank account demonstrating error handling techniques."""
    
    def __init__(self, account_id, owner_name, initial_balance=0):
        """
        Initialize a new bank account.
        
        Args:
            account_id: Unique account identifier
            owner_name: Name of the account owner
            initial_balance: Starting balance (default 0)
            
        Raises:
            InvalidInputError: If any input parameters are invalid
        """
        try:
            # Syntax error handling: validate input formats
            self.account_id = InputValidator.validate_account_id(account_id)
            
            # Logical error prevention: validate name is not empty
            if not isinstance(owner_name, str) or not owner_name.strip():
                raise InvalidInputError("Owner name cannot be empty", "E006")
                
            self.owner_name = owner_name
            self.balance = InputValidator.validate_amount(initial_balance)
            self.transaction_history = []
            
        except BankingException as e:
            # Runtime exception handling: re-raise
            raise

    def deposit(self, amount):
        """
        Deposit funds into the account.
        
        Args:
            amount: Amount to deposit
            
        Returns:
            Decimal: New account balance
            
        Raises:
            InvalidAmountError: If amount is invalid
            BankingException: If a logical error occurs
        """
        try:
            # Syntax error handling: validate amount format
            amount = InputValidator.validate_amount(amount)
            
            # Record transaction
            transaction = {
                'type': 'deposit',
                'amount': amount,
                'status': 'pending'
            }
            
            # Update balance
            previous_balance = self.balance
            self.balance += amount
            
            # Logical error check: ensure new balance is greater than old balance
            if self.balance <= previous_balance:
                transaction['status'] = 'failed'
                transaction['error'] = "Logical error in deposit: Balance didn't increase"
                self.transaction_history.append(transaction)
                raise BankingException("Logical error in deposit: Balance didn't increase", "L001")
            
            # Update transaction status
            transaction['status'] = 'completed'
            self.transaction_history.append(transaction)
            
            return self.balance
            
        except BankingException as e:
            # Runtime exception handling
            if not any(t.get('error') == str(e) for t in self.transaction_history):
                self.transaction_history.append({
                    'type': 'deposit',
                    'amount': amount if 'amount' in locals() else None,
                    'status': 'failed',
                    'error': str(e)
                })
            raise

    def withdraw(self, amount):
        """
        Withdraw funds from the account.
        
        Args:
            amount: Amount to withdraw
            
        Returns:
            Decimal: New account balance
            
        Raises:
            InvalidAmountError: If amount is invalid
            InsufficientFundsError: If insufficient funds are available
            BankingException: If a logical error occurs
        """
        try:
            # Syntax error handling: validate amount format
            amount = InputValidator.validate_amount(amount)
            
            # Record transaction
            transaction = {
                'type': 'withdrawal',
                'amount': amount,
                'status': 'pending'
            }
            
            # Runtime exception handling: check for sufficient funds
            if amount > self.balance:
                transaction['status'] = 'failed'
                transaction['error'] = f"Insufficient funds"
                self.transaction_history.append(transaction)
                raise InsufficientFundsError(self.account_id, amount, self.balance)
                
            # Update balance
            previous_balance = self.balance
            self.balance -= amount
            
            # Logical error check: ensure new balance is less than old balance
            if self.balance >= previous_balance:
                transaction['status'] = 'failed'
                transaction['error'] = "Logical error in withdrawal: Balance didn't decrease"
                self.transaction_history.append(transaction)
                raise BankingException("Logical error in withdrawal: Balance didn't decrease", "L002")
            
            # Update transaction status
            transaction['status'] = 'completed'
            self.transaction_history.append(transaction)
            
            return self.balance
            
        except BankingException as e:
            # Runtime exception handling
            if not any(t.get('error') == str(e) for t in self.transaction_history):
                self.transaction_history.append({
                    'type': 'withdrawal',
                    'amount': amount if 'amount' in locals() else None,
                    'status': 'failed',
                    'error': str(e)
                })
            raise

    def get_balance(self):
        """Get the current account balance."""
        return self.balance

    def get_transaction_history(self):
        """Get the transaction history for the account."""
        return self.transaction_history

def transfer(from_account, to_account, amount):
    """
    Transfer funds between accounts with transaction integrity.
    
    Args:
        from_account: Source account
        to_account: Destination account
        amount: Amount to transfer
        
    Returns:
        dict: Transaction details including new balances
        
    Raises:
        InvalidAmountError: If amount is invalid
        InsufficientFundsError: If source account has insufficient funds
    """
    # Syntax error handling: validate amount
    amount = InputValidator.validate_amount(amount)
    
    # Runtime error handling: check sufficient funds
    if amount > from_account.balance:
        raise InsufficientFundsError(
            from_account.account_id, 
            amount, 
            from_account.balance
        )
    
    # Perform withdrawal from source account
    initial_balance = from_account.balance
    from_account.balance -= amount
    
    try:
        # Perform deposit to destination account
        to_account.deposit(amount)
        
        # Logical error check: ensure money is conserved
        total_before = initial_balance + to_account.balance - amount
        total_after = from_account.balance + to_account.balance
        
        if total_before != total_after:
            # Logical error detected - rollback and raise exception
            from_account.balance = initial_balance
            raise BankingException("Logical error: Money not conserved during transfer", "L003")
        
        # Return transaction details
        return {
            'from_balance': from_account.balance,
            'to_balance': to_account.balance,
            'amount': amount,
            'status': 'completed'
        }
        
    except BankingException as e:
        # If deposit fails, rollback the withdrawal
        from_account.balance = initial_balance
        
        # Re-raise the exception
        raise

def main():
    """Main function demonstrating error handling for all three error types."""
    print("Banking System Error Handling Demo")
    print("==================================")
    
    try:
        # Create account - demonstrates input validation (syntax error handling)
        print("\n1. Creating account with proper values...")
        account1 = BankAccount("ACCT123456", "John Doe", 1000)
        print(f"   Success! Balance: ${account1.get_balance()}")
        
        print("\n2. Creating account with invalid ID (syntax error)...")
        try:
            account2 = BankAccount("AC", "Jane Doe", 500)  # Too short
        except InvalidInputError as e:
            print(f"   Caught error: {e}")
        
        # Create second valid account for transfers
        account2 = BankAccount("ACCT654321", "Jane Doe", 500)
        
        # Demonstrate runtime exception handling
        print("\n3. Withdrawing with insufficient funds (runtime error)...")
        try:
            account1.withdraw(2000)  # More than available
        except InsufficientFundsError as e:
            print(f"   Caught error: {e}")
        
        # Demonstrate logical error prevention
        print("\n4. Transfer with transaction integrity...")
        initial_total = account1.get_balance() + account2.get_balance()
        print(f"   Initial total money in system: ${initial_total}")
        
        result = transfer(account1, account2, 200)
        print(f"   Transfer completed.")
        print(f"   Account 1 balance: ${account1.get_balance()}")
        print(f"   Account 2 balance: ${account2.get_balance()}")
        
        final_total = account1.get_balance() + account2.get_balance()
        print(f"   Final total money in system: ${final_total}")
        
        # Verify no money was created or destroyed (logical error check)
        assert initial_total == final_total, "Money was created or destroyed"
        print("   Logical integrity verified: No money created or destroyed.")
        
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
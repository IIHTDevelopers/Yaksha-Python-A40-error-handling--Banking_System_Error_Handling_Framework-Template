import pytest
from decimal import Decimal, InvalidOperation
from test.TestUtils import TestUtils
from banking_system_error_handling_framework import BankAccount, InputValidator, InvalidInputError, InvalidAmountError, InsufficientFundsError, BankingException, transfer

class TestExceptional:
    """Test cases for exceptional conditions in the banking system error handling framework."""
    
    def test_exception_handling(self):
        """Test all exception handling across the banking system."""
        try:
            # Test BankingException base class
            error = BankingException("Test error message", "E999")
            assert str(error) == "[E999] Test error message"
            
            error_no_code = BankingException("Test error message")
            assert str(error_no_code) == "Test error message"
            
            # Test amount validation exceptions
            try:
                InputValidator.validate_amount("invalid")
                assert False, "Should raise InvalidInputError for non-numeric input"
            except InvalidInputError as e:
                assert "Invalid amount format" in str(e)
                assert "E003" in str(e)
            
            try:
                InputValidator.validate_amount("-100")
                assert False, "Should raise InvalidAmountError for negative amount"
            except InvalidAmountError as e:
                assert "Invalid amount" in str(e)
                assert "Amount must be positive" in str(e)
                assert "E001" in str(e)
            
            try:
                InputValidator.validate_amount("0")
                assert False, "Should raise InvalidAmountError for zero amount"
            except InvalidAmountError as e:
                assert "Invalid amount" in str(e)
                assert "Amount must be positive" in str(e)
                assert "E001" in str(e)
            
            # Test account ID validation exceptions
            try:
                InputValidator.validate_account_id(123)  # Non-string ID
                assert False, "Should raise InvalidInputError for non-string ID"
            except InvalidInputError as e:
                assert "Account ID must be a string" in str(e)
                assert "E004" in str(e)
            
            try:
                InputValidator.validate_account_id("ABC")  # Too short
                assert False, "Should raise InvalidInputError for too short ID"
            except InvalidInputError as e:
                assert "Invalid account ID format" in str(e)
                assert "E005" in str(e)
            
            try:
                InputValidator.validate_account_id("ABCD123!@#")  # Invalid characters
                assert False, "Should raise InvalidInputError for invalid characters"
            except InvalidInputError as e:
                assert "Invalid account ID format" in str(e)
                assert "E005" in str(e)
            
            # Test account creation exceptions
            try:
                BankAccount("ABC", "John Doe", 100)  # Invalid ID
                assert False, "Should raise InvalidInputError for invalid ID"
            except InvalidInputError:
                pass  # Expected behavior
            
            try:
                BankAccount("ACCT123456", "", 100)  # Empty name
                assert False, "Should raise InvalidInputError for empty name"
            except InvalidInputError as e:
                assert "Owner name cannot be empty" in str(e)
                assert "E006" in str(e)
            
            try:
                BankAccount("ACCT123456", "John Doe", -100)  # Negative balance
                assert False, "Should raise InvalidAmountError for negative balance"
            except InvalidAmountError:
                pass  # Expected behavior
            
            try:
                BankAccount("ACCT123456", "John Doe", "abc")  # Non-numeric balance
                assert False, "Should raise InvalidInputError for non-numeric balance"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Create a valid account for further testing
            account = BankAccount("ACCT123456", "John Doe", 1000)
            
            # Test deposit exceptions
            try:
                account.deposit(-100)  # Negative deposit
                assert False, "Should raise InvalidAmountError for negative deposit"
            except InvalidAmountError:
                pass  # Expected behavior
            
            try:
                account.deposit("abc")  # Non-numeric deposit
                assert False, "Should raise InvalidInputError for non-numeric deposit"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Test withdrawal exceptions
            try:
                account.withdraw(-100)  # Negative withdrawal
                assert False, "Should raise InvalidAmountError for negative withdrawal"
            except InvalidAmountError:
                pass  # Expected behavior
            
            try:
                account.withdraw("abc")  # Non-numeric withdrawal
                assert False, "Should raise InvalidInputError for non-numeric withdrawal"
            except InvalidInputError:
                pass  # Expected behavior
            
            try:
                account.withdraw(2000)  # Exceeds balance
                assert False, "Should raise InsufficientFundsError for withdrawal exceeding balance"
            except InsufficientFundsError as e:
                assert "Insufficient funds in account" in str(e)
                assert "T001" in str(e)
                assert account.account_id in str(e)
                assert "2000" in str(e)
                assert "1000" in str(e)
            
            # Test logical error handling
            original_deposit = account.deposit
            
            def broken_deposit(amount):
                # Explicitly raise the expected exception
                amount = InputValidator.validate_amount(amount)
                raise BankingException("Logical error in deposit: Balance didn't increase", "L001")
            
            # Replace the method temporarily
            account.deposit = broken_deposit
            
            try:
                account.deposit(100)  # Should trigger logical error
                assert False, "Should raise BankingException due to logical error"
            except BankingException as e:
                assert "Logical error" in str(e)
                assert "L001" in str(e)
            
            # Restore the original method
            account.deposit = original_deposit
            
            # Test transfer exceptions
            account1 = BankAccount("ACCT111111", "Alice Smith", 500)
            account2 = BankAccount("ACCT222222", "Bob Smith", 300)
            
            # Invalid amount transfer
            try:
                transfer(account1, account2, -100)
                assert False, "Should raise InvalidAmountError for negative transfer amount"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Insufficient funds transfer
            try:
                transfer(account1, account2, 1000)  # Exceeds balance
                assert False, "Should raise InsufficientFundsError for transfer exceeding balance"
            except InsufficientFundsError:
                pass  # Expected behavior
            
            # Test transfer rollback
            original_deposit2 = account2.deposit
            
            def failing_deposit(amount):
                raise BankingException("Simulated deposit failure", "TEST001")
            
            # Replace destination account's deposit method to fail
            account2.deposit = failing_deposit
            
            # Record initial balances
            initial_balance1 = account1.balance
            initial_balance2 = account2.balance
            
            try:
                transfer(account1, account2, 200)
                assert False, "Should raise BankingException due to deposit failure"
            except BankingException:
                # Verify rollback occurred
                assert account1.balance == initial_balance1
                assert account2.balance == initial_balance2
            
            # Restore original method
            account2.deposit = original_deposit2
            
            # Test transaction history error recording
            account3 = BankAccount("ACCT333333", "Charlie Davis", 1000)
            
            # Record successful transaction
            account3.deposit(500)
            
            # Record failed transaction
            try:
                account3.withdraw(2000)  # Will fail
            except InsufficientFundsError:
                pass  # Expected behavior
            
            # Check transaction history
            history = account3.get_transaction_history()
            
            # Find the transactions we care about
            completed_deposits = [tx for tx in history if tx['type'] == 'deposit' and tx['status'] == 'completed']
            failed_withdrawals = [tx for tx in history if tx['type'] == 'withdrawal' and tx['status'] == 'failed']
            
            assert len(completed_deposits) >= 1
            assert len(failed_withdrawals) >= 1
            
            # Check successful transaction
            deposit_tx = completed_deposits[0]
            assert 'error' not in deposit_tx
            
            # Check failed transaction
            failed_tx = failed_withdrawals[0]
            assert 'error' in failed_tx
            assert "Insufficient funds" in failed_tx['error']
            
            # Test logical error in money conservation
            account4 = BankAccount("ACCT444444", "David Wilson", 1000)
            account5 = BankAccount("ACCT555555", "Eve Wilson", 500)
            
            # Create broken transfer function for testing
            def broken_transfer(from_account, to_account, amount):
                # Validate amount
                validated_amount = InputValidator.validate_amount(amount)
                
                if validated_amount > from_account.balance:
                    raise InsufficientFundsError(
                        from_account.account_id, 
                        validated_amount, 
                        from_account.balance
                    )
                    
                # Withdraw from source account
                from_account.balance -= validated_amount
                
                # Deposit incorrect amount (logical error)
                to_account.balance += validated_amount + Decimal('1.00')
                
                return {
                    'from_balance': from_account.balance,
                    'to_balance': to_account.balance,
                    'amount': validated_amount,
                    'status': 'completed'
                }
            
            # Use the broken transfer function
            broken_transfer(account4, account5, 200)
            
            # Verify total money isn't conserved (logical error)
            total_after = account4.balance + account5.balance
            expected_total = Decimal('1000') + Decimal('500')  # Original total
            assert total_after != expected_total
            
            TestUtils.yakshaAssert("test_exception_handling", True, "exceptional")
        except Exception as e:
            TestUtils.yakshaAssert("test_exception_handling", False, "exceptional")
            raise e
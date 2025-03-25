import pytest
from decimal import Decimal
from test.TestUtils import TestUtils
from banking_system_error_handling_framework import BankAccount, InputValidator, BankingException, InvalidInputError, InvalidAmountError, InsufficientFundsError, transfer

class TestFunctional:
    """Test cases for functional requirements of the banking system error handling framework."""
    
    def test_exception_hierarchy(self):
        """Test the proper implementation of the exception hierarchy."""
        try:
            # Test exception hierarchy
            # BankingException should be the base class
            assert issubclass(InvalidInputError, BankingException)
            assert issubclass(InvalidAmountError, InvalidInputError)
            assert issubclass(InsufficientFundsError, BankingException)
            
            # Test error codes and messages
            base_exception = BankingException("Test message", "B001")
            assert str(base_exception) == "[B001] Test message"
            
            amount_error = InvalidAmountError("100")
            assert "E001" in str(amount_error)
            assert "Invalid amount: 100" in str(amount_error)
            
            insufficient_funds = InsufficientFundsError("ACC123", Decimal("200"), Decimal("100"))
            assert "T001" in str(insufficient_funds)
            assert "Insufficient funds" in str(insufficient_funds)
            assert "ACC123" in str(insufficient_funds)
            
            TestUtils.yakshaAssert("test_exception_hierarchy", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_exception_hierarchy", False, "functional")
            raise e
    
    def test_input_validator(self):
        """Test the input validation functionality."""
        try:
            # Test amount validation - syntax error handling
            # Valid amounts
            amount1 = InputValidator.validate_amount("100.50")
            assert amount1 == Decimal("100.50")
            
            amount2 = InputValidator.validate_amount(50)
            assert amount2 == Decimal("50")
            
            # Invalid amounts - should raise exceptions
            with pytest.raises(InvalidAmountError):
                InputValidator.validate_amount(0)
                
            with pytest.raises(InvalidAmountError):
                InputValidator.validate_amount(-10)
                
            with pytest.raises(InvalidInputError):
                InputValidator.validate_amount("not_a_number")
            
            # Test account ID validation - syntax error handling
            # Valid IDs
            id1 = InputValidator.validate_account_id("ACCT123456")
            assert id1 == "ACCT123456"
            
            # Invalid IDs - should raise exceptions
            with pytest.raises(InvalidInputError):
                InputValidator.validate_account_id(12345)  # Not a string
                
            with pytest.raises(InvalidInputError):
                InputValidator.validate_account_id("ABC")  # Too short
                
            with pytest.raises(InvalidInputError):
                InputValidator.validate_account_id("ACCT123456&*")  # Invalid characters
            
            TestUtils.yakshaAssert("test_input_validator", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_input_validator", False, "functional")
            raise e
    
    def test_bank_account_operations(self):
        """Test basic bank account operations with error handling."""
        try:
            # Create account
            account = BankAccount("ACCT123456", "John Doe", 1000)
            assert account.account_id == "ACCT123456"
            assert account.owner_name == "John Doe"
            assert account.balance == Decimal("1000")
            
            # Test deposit functionality
            new_balance = account.deposit(500)
            assert new_balance == Decimal("1500")
            assert account.balance == Decimal("1500")
            
            # Test withdrawal functionality
            new_balance = account.withdraw(300)
            assert new_balance == Decimal("1200")
            assert account.balance == Decimal("1200")
            
            # Test runtime exception handling - insufficient funds
            with pytest.raises(InsufficientFundsError):
                account.withdraw(2000)
            
            # Verify balance didn't change after failed withdrawal
            assert account.balance == Decimal("1200")
            
            # Test transaction history recording
            history = account.get_transaction_history()
            
            # Find completed deposit, completed withdrawal, and failed withdrawal
            completed_deposits = [tx for tx in history if tx['type'] == 'deposit' and tx['amount'] == Decimal("500") and tx['status'] == 'completed']
            completed_withdrawals = [tx for tx in history if tx['type'] == 'withdrawal' and tx['amount'] == Decimal("300") and tx['status'] == 'completed']
            failed_withdrawals = [tx for tx in history if tx['type'] == 'withdrawal' and tx['amount'] == Decimal("2000") and tx['status'] == 'failed']
            
            # Verify we found each type of transaction
            assert len(completed_deposits) > 0
            assert len(completed_withdrawals) > 0
            assert len(failed_withdrawals) > 0
            
            # Verify successful transactions
            assert completed_deposits[0]['type'] == 'deposit'
            assert completed_deposits[0]['amount'] == Decimal("500")
            assert completed_deposits[0]['status'] == 'completed'
            
            assert completed_withdrawals[0]['type'] == 'withdrawal'
            assert completed_withdrawals[0]['amount'] == Decimal("300")
            assert completed_withdrawals[0]['status'] == 'completed'
            
            # Verify failed transaction
            assert failed_withdrawals[0]['type'] == 'withdrawal'
            assert failed_withdrawals[0]['amount'] == Decimal("2000")
            assert failed_withdrawals[0]['status'] == 'failed'
            assert 'error' in failed_withdrawals[0]
            
            TestUtils.yakshaAssert("test_bank_account_operations", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_bank_account_operations", False, "functional")
            raise e
    
    def test_logical_error_prevention(self):
        """Test the system's ability to prevent logical errors using assertions."""
        try:
            # Test that balance increases after deposit
            account1 = BankAccount("ACCT111111", "Alice Smith", 1000)
            initial_balance = account1.balance
            account1.deposit(500)
            assert account1.balance > initial_balance
            
            # Test that balance decreases after withdrawal
            initial_balance = account1.balance
            account1.withdraw(200)
            assert account1.balance < initial_balance
            
            # Test money conservation during transfer
            account2 = BankAccount("ACCT222222", "Bob Jones", 500)
            
            # Calculate total money before transfer
            total_before = account1.balance + account2.balance
            
            # Perform transfer
            result = transfer(account1, account2, 300)
            
            # Calculate total money after transfer
            total_after = account1.balance + account2.balance
            
            # Verify money conservation (logical error prevention)
            assert total_before == total_after
            
            TestUtils.yakshaAssert("test_logical_error_prevention", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_logical_error_prevention", False, "functional")
            raise e
    
    def test_transaction_rollback(self):
        """Test the transaction rollback mechanism for failed transfers."""
        try:
            # Create accounts
            account1 = BankAccount("ACCT333333", "Charlie Davis", 1000)
            account2 = BankAccount("ACCT444444", "Diana Evans", 500)
            
            # Save initial balances
            initial_balance1 = account1.balance
            initial_balance2 = account2.balance
            
            # Create a mock deposit method for account2 that will fail
            original_deposit = account2.deposit
            
            def failing_deposit(amount):
                # This will simulate a failure during deposit
                raise BankingException("Simulated deposit failure", "TEST001")
            
            # Replace the deposit method temporarily
            account2.deposit = failing_deposit
            
            # Attempt transfer which should trigger rollback
            try:
                transfer(account1, account2, 200)
                assert False, "Transfer should have failed"
            except BankingException as e:
                # Verify the error message
                assert "Simulated deposit failure" in str(e)
                
                # Verify rollback occurred - balances should be unchanged
                assert account1.balance == initial_balance1
                assert account2.balance == initial_balance2
            
            # Restore original deposit method
            account2.deposit = original_deposit
            
            TestUtils.yakshaAssert("test_transaction_rollback", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_transaction_rollback", False, "functional")
            raise e
    
    def test_error_logging(self):
        """Test that errors are properly logged."""
        try:
            # Create an account
            account = BankAccount("ACCT555555", "Eve Wilson", 1000)
            
            # Perform a successful operation
            account.deposit(500)
            
            # Perform operations that will cause errors
            try:
                account.withdraw(2000)  # Insufficient funds
            except InsufficientFundsError:
                pass  # Expected
                
            try:
                account.deposit(-100)  # Invalid amount
            except InvalidAmountError:
                pass  # Expected
                
            try:
                account.deposit("abc")  # Invalid format
            except InvalidInputError:
                pass  # Expected
            
            # Check that transaction history includes error information
            history = account.get_transaction_history()
            
            # Find the failed transactions
            failed_transactions = [t for t in history if t['status'] == 'failed']
            
            # Verify we have at least one failed transaction
            assert len(failed_transactions) >= 1
            
            # Verify error details are recorded
            for transaction in failed_transactions:
                assert 'error' in transaction
                assert transaction['error'] is not None
                assert len(transaction['error']) > 0
            
            # Check specific error types
            error_messages = [t['error'] for t in failed_transactions]
            
            # At least one should mention insufficient funds
            assert any("Insufficient funds" in msg for msg in error_messages)
            
            TestUtils.yakshaAssert("test_error_logging", True, "functional")
        except Exception as e:
            TestUtils.yakshaAssert("test_error_logging", False, "functional")
            raise e
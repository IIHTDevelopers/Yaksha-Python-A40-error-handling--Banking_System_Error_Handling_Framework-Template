import pytest
from decimal import Decimal
from test.TestUtils import TestUtils
from banking_system_error_handling_framework import BankAccount, InputValidator, InvalidInputError, InvalidAmountError, InsufficientFundsError, BankingException, transfer

class TestBoundary:
    """Test cases for boundary conditions in the banking system error handling framework."""
    
    def test_system_boundaries(self):
        """Test all boundary conditions for the banking system."""
        try:
            # Test InputValidator boundary conditions
            # Valid amounts
            assert InputValidator.validate_amount("100") == Decimal("100")
            assert InputValidator.validate_amount("0.01") == Decimal("0.01")
            assert InputValidator.validate_amount(Decimal("100.50")) == Decimal("100.50")
            
            # Invalid amounts - zero
            try:
                InputValidator.validate_amount("0")
                assert False, "Should raise InvalidAmountError for zero amount"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Invalid amounts - negative
            try:
                InputValidator.validate_amount("-10")
                assert False, "Should raise InvalidAmountError for negative amount"
            except InvalidAmountError:
                pass  # Expected behavior
                
            # Invalid amounts - non-numeric
            try:
                InputValidator.validate_amount("abc")
                assert False, "Should raise InvalidInputError for non-numeric input"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Valid IDs
            assert InputValidator.validate_account_id("ACCT123456") == "ACCT123456"
            assert InputValidator.validate_account_id("12345678") == "12345678"
            assert InputValidator.validate_account_id("ABCDEFGHIJ") == "ABCDEFGHIJ"
            
            # Invalid IDs - too short
            try:
                InputValidator.validate_account_id("ACCT")
                assert False, "Should raise InvalidInputError for too short ID"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Invalid IDs - too long
            try:
                InputValidator.validate_account_id("ACCT123456789")
                assert False, "Should raise InvalidInputError for too long ID"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Invalid IDs - non-alphanumeric
            try:
                InputValidator.validate_account_id("ACCT-123!")
                assert False, "Should raise InvalidInputError for non-alphanumeric ID"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Valid account creation
            account1 = BankAccount("ACCT123456", "John Doe", 1000)
            assert account1.account_id == "ACCT123456"
            assert account1.owner_name == "John Doe"
            assert account1.balance == Decimal("1000")
            
            # Invalid account creation - invalid ID
            try:
                BankAccount("A", "John Doe", 1000)
                assert False, "Should raise InvalidInputError for invalid ID"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Invalid account creation - empty name
            try:
                BankAccount("ACCT123456", "", 1000)
                assert False, "Should raise InvalidInputError for empty name"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Invalid account creation - invalid initial balance
            try:
                BankAccount("ACCT123456", "John Doe", -100)
                assert False, "Should raise InvalidAmountError for negative balance"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Test deposit and withdrawal
            account2 = BankAccount("ACCT654321", "Jane Doe", 500)
            
            # Valid deposits
            assert account2.deposit("100") == Decimal("600")
            assert account2.deposit(0.01) == Decimal("600.01")  # Minimum valid amount
            
            # Invalid deposit - zero
            try:
                account2.deposit(0)
                assert False, "Should raise InvalidAmountError for zero deposit"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Invalid deposit - negative
            try:
                account2.deposit(-50)
                assert False, "Should raise InvalidAmountError for negative deposit"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Invalid deposit - non-numeric
            try:
                account2.deposit("abc")
                assert False, "Should raise InvalidInputError for non-numeric deposit"
            except InvalidInputError:
                pass  # Expected behavior
            
            # Valid withdrawals
            assert account2.withdraw("0.01") == Decimal("600.00")
            assert account2.withdraw(100) == Decimal("500.00")
            
            # Invalid withdrawal - zero
            try:
                account2.withdraw(0)
                assert False, "Should raise InvalidAmountError for zero withdrawal"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Invalid withdrawal - negative
            try:
                account2.withdraw(-50)
                assert False, "Should raise InvalidAmountError for negative withdrawal"
            except InvalidAmountError:
                pass  # Expected behavior
            
            # Invalid withdrawal - exceeding balance
            try:
                account2.withdraw(600)  # Balance is 500
                assert False, "Should raise InsufficientFundsError for withdrawal exceeding balance"
            except InsufficientFundsError:
                pass  # Expected behavior
            
            # Test transfer
            account3 = BankAccount("ACCT111111", "Alice Smith", 1000)
            account4 = BankAccount("ACCT222222", "Bob Smith", 500)
            
            # Valid transfer
            result = transfer(account3, account4, 200)
            assert result['status'] == 'completed'
            assert account3.balance == Decimal("800")
            assert account4.balance == Decimal("700")
            
            # Invalid transfer - exceeding source balance
            try:
                transfer(account3, account4, 1000)  # Balance is 800
                assert False, "Should raise InsufficientFundsError for transfer exceeding balance"
            except InsufficientFundsError:
                pass  # Expected behavior
                
            # Logical error check - verify money conservation
            total_before = account3.balance + account4.balance
            transfer(account3, account4, 100)
            total_after = account3.balance + account4.balance
            assert total_before == total_after, "Total money should remain constant during transfer"
            
            # Test transaction history
            account5 = BankAccount("ACCT333333", "Carol Brown", 1000)
            account5.deposit(200)
            account5.withdraw(100)
            
            history = account5.get_transaction_history()
            assert len(history) >= 2
            
            # Find the deposit and withdrawal transactions
            deposit_tx = next((tx for tx in history if tx['type'] == 'deposit' and tx['amount'] == Decimal("200")), None)
            withdraw_tx = next((tx for tx in history if tx['type'] == 'withdrawal' and tx['amount'] == Decimal("100")), None)
            
            assert deposit_tx is not None
            assert withdraw_tx is not None
            assert deposit_tx['status'] == 'completed'
            assert withdraw_tx['status'] == 'completed'
            
            # Test failed transaction recording
            try:
                account5.withdraw(2000)  # Will fail
            except InsufficientFundsError:
                pass
                
            history = account5.get_transaction_history()
            failed_withdrawals = [tx for tx in history if tx['type'] == 'withdrawal' and tx['status'] == 'failed' and tx['amount'] == Decimal("2000")]
            assert len(failed_withdrawals) > 0
            assert 'error' in failed_withdrawals[0]
            
            TestUtils.yakshaAssert("test_system_boundaries", True, "boundary")
        except Exception as e:
            TestUtils.yakshaAssert("test_system_boundaries", False, "boundary")
            raise e
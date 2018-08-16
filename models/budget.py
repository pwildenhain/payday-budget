# Import modules
from datetime import datetime
from sqlite3 import connect
from pandas import DataFrame, read_sql
# Define classes
class Account():
    """An account within a personal budget

    Attributes:
        name (str): Display name
        category (str): Budget category
        budgeted_amount (int): Bi-weekly allocated amount
        current_balance (int): Current surplus/shortage of allocated amount
        transaction_history (list(tuple)): Every transaction recorded on this account
    """

    def __init__(self, name, category, budgeted_amount, current_balance, transaction_history):
        self.name = name
        self.category = category
        self.budgeted_amount = budgeted_amount
        self.current_balance = current_balance
        self.transaction_history = transaction_history

    def update_budgeted_amount(self, new_budgeted_amount):
        """Update the current budgeted amount for the account"""
        try:
            if new_budgeted_amount > 0:
                self.budgeted_amount = new_budgeted_amount
            else:
                return print('Amount must be greater than zero')
        except TypeError:
            print('Amount must be a number')

    def update_current_balance(self, transaction_type, amount):
        """When a transaction is recorded, update the current balance left on the account"""
        if transaction_type == 'debit':
            self.current_balance -= amount
        elif transaction_type == 'credit':
            self.current_balance += amount

    def add_transaction(self, comment, transaction_type, amount):
        """Record a transaction on the account transaction history and update the current balance"""
        try:
            self.update_current_balance(transaction_type, amount)
        except TypeError:
            print('Amount must be a number')
        else:
            date = datetime.now().strftime('%Y-%m-%d')
            transaction = (date, self.name, comment, transaction_type, amount)
            self.transaction_history.append(transaction)
        
class Budget():
    """A bi-weekly personal budget

    Attributes:
        accounts (dict(:obj:)): A dict of Account() objects
    """

    def __init__(self, accounts = {}, categories = []):
        self.accounts = accounts
        self.categories = categories

    def add_account(self, **kwargs):
        """Add an account to the existing budget accounts"""
        new_account = kwargs['name']
        self.accounts[new_account] = Account(**kwargs)
        new_account_obj = self.accounts[new_account]
        insert_account = [( 
            new_account_obj.category,
            new_account_obj.name,
            new_account_obj.budgeted_amount,
            new_account_obj.current_balance
            )]
        labels = ['category', 'name', 'budgeted_amount', 'balance']
        insert_df = DataFrame.from_records(insert_account, columns=labels)
        conn = connect('data/budget.db')
        insert_df.to_sql("budget_summary", conn, if_exists='append', index=False)
        conn.close()

    def transfer_money(self, origin, destination, amount):
        try:
            self.accounts[origin].add_transaction(f'Transfer to {destination}', 'debit', amount)
        except KeyError:
            print(f'{origin} is not an account in the budget')
        try:
            self.accounts[destination].add_transaction(f'Transfer from {origin}', 'credit', amount)
        except KeyError:
            print(f'{destination} is not an account in the budget')

    def payday(self):
        for account in self.accounts:
            account_obj = self.accounts[account]
            account_obj.add_transaction('Payday', 'credit', account_obj.budgeted_amount)

    def display_summary(self):
        """Display the current balance compared to the budgeted amount for each account"""
        conn = connect('data/budget.db')
        display_df = read_sql('''
        SELECT 
        category as Category
        , name as Account
        , budgeted_amount as "Budgeted"
        , balance as Balance
        FROM 
        budget_summary 
        ORDER BY
        category, budgeted_amount DESC''',
        conn
        )
        conn.close()
        print(display_df)


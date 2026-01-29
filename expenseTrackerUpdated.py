"""
💰 EXPENSE TRACKER APPLICATION
A complete personal finance management system with MySQL database

"""

# ============================================================================
# IMPORTS
# ============================================================================
import mysql.connector
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import hashlib
import sys
import google.generativeai as genai
import os
os.environ['GRPC_DNS_RESOLVER'] = 'native'
genai.configure(api_key="AIzaSyBL6ZhW4v1cildkPNw85AU5hQEfAIXE7T8")

# ============================================================================
# DATABASE CONNECTION
# ============================================================================
def create_connection():
    """Create and return MySQL database connection"""
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",  # ← Change to your MySQL username
            password="1234",  # ← Change to your MySQL password
            database="expense_tracker"
        )
        print("✅ Connected to MySQL database")
        return conn
    except mysql.connector.Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        print("Make sure:")
        print("  1. MySQL server is running")
        print("  2. Database 'expense_tracker' exists")
        print("  3. Username and password are correct")
        sys.exit(1)

# ============================================================================
# DATABASE SETUP
# ============================================================================
def create_tables(conn):
    """Create all required database tables"""
    cursor = conn.cursor()
    
    try:
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            monthly_budget DECIMAL(10,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Expenses table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            date DATE NOT NULL,
            category VARCHAR(50) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        
        # Income table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            date DATE NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()
        print("✅ Database tables created successfully")
        
    except mysql.connector.Error as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)
    finally:
        cursor.close()

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def clear_screen():
    """Clear the console screen"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

# ============================================================================
# USER AUTHENTICATION
# ============================================================================
def signup(conn):
    """Handle user registration"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("📝 USER REGISTRATION")
    print("="*50)
    
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    confirm_password = input("Confirm password: ").strip()
    
    # Validation
    if password != confirm_password:
        print("❌ Passwords don't match!")
        cursor.close()
        return
    
    if len(password) < 3:
        print("❌ Password must be at least 6 characters!")
        cursor.close()
        return
    
    try:
        monthly_budget = float(input("Enter monthly budget: "))
        if monthly_budget <= 0:
            print("❌ Budget must be positive!")
            cursor.close()
            return
    except ValueError:
        print("❌ Invalid budget amount!")
        cursor.close()
        return
    
    # Insert into database
    try:
        hashed_pw = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, monthly_budget) VALUES (%s, %s, %s)",
            (username, hashed_pw, monthly_budget)
        )
        conn.commit()
        print(f"✅ User '{username}' created successfully!")
    except mysql.connector.IntegrityError:
        print("❌ Username already exists!")
    except mysql.connector.Error as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()

def login(conn):
    """Handle user login and return user_id and monthly_budget"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("🔐 USER LOGIN")
    print("="*50)
    
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    hashed_pw = hash_password(password)
    
    cursor.execute(
        "SELECT id, monthly_budget FROM users WHERE username=%s AND password=%s",
        (username, hashed_pw)
    )
    result = cursor.fetchone()
    cursor.close()
    
    if result:
        print(f"✅ Welcome back, {username}!")
        return result[0], result[1]  # user_id, monthly_budget
    else:
        print("❌ Invalid username or password!")
        return None, None

# ============================================================================
# EXPENSE MANAGEMENT
# ============================================================================
def add_expense(conn, user_id):
    """Add a new expense"""
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*50)
        print("➕ ADD EXPENSE")
        print("="*50)
        
        date_input = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not date_input:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            # Validate date format
            datetime.strptime(date_input, "%Y-%m-%d")
            date = date_input
        
        category = input("Category (Food/Transport/Shopping/Bills/Entertainment/Other): ").strip()
        amount = float(input("Amount: "))
        description = input("Description: ").strip()
        
        if amount <= 0:
            print("❌ Amount must be positive!")
            return
        
        cursor.execute(
            "INSERT INTO expenses (user_id, date, category, amount, description) VALUES (%s, %s, %s, %s, %s)",
            (user_id, date, category, amount, description)
        )
        conn.commit()
        print("✅ Expense added successfully!")
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()

def view_expenses(conn, user_id):
    """Display all expenses for the user"""
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, date, category, amount, description FROM expenses WHERE user_id=%s ORDER BY date DESC",
        (user_id,)
    )
    expenses = cursor.fetchall()
    cursor.close()
    
    if not expenses:
        print("\n📭 No expenses found")
        return
    
    print("\n" + "="*80)
    print(f"{'ID':<5} {'Date':<12} {'Category':<15} {'Amount':<10} {'Description':<30}")
    print("="*80)
    for exp in expenses:
        print(f"{exp[0]:<5} {str(exp[1]):<12} {exp[2]:<15} ₹{exp[3]:<9.2f} {exp[4]:<30}")
    print("="*80)

def edit_expense(conn, user_id):
    """Edit an existing expense"""
    cursor = conn.cursor()
    
    view_expenses(conn, user_id)
    
    try:
        exp_id = int(input("\nEnter Expense ID to edit: "))
        
        cursor.execute(
            "SELECT * FROM expenses WHERE id=%s AND user_id=%s",
            (exp_id, user_id)
        )
        expense = cursor.fetchone()
        
        if not expense:
            print("❌ Expense not found or doesn't belong to you!")
            return
        
        print(f"\nCurrent: Date={expense[2]}, Category={expense[3]}, Amount=₹{expense[4]}, Description={expense[5]}")
        print("Press Enter to keep current value\n")
        
        # Get new values
        new_date = input(f"New Date (current: {expense[2]}): ").strip()
        if new_date:
            datetime.strptime(new_date, "%Y-%m-%d")  # Validate
        else:
            new_date = expense[2]
        
        new_category = input(f"New Category (current: {expense[3]}): ").strip()
        new_category = new_category if new_category else expense[3]
        
        new_amount = input(f"New Amount (current: {expense[4]}): ").strip()
        if new_amount:
            new_amount = float(new_amount)
            if new_amount <= 0:
                print("❌ Amount must be positive!")
                return
        else:
            new_amount = expense[4]
        
        new_description = input(f"New Description (current: {expense[5]}): ").strip()
        new_description = new_description if new_description else expense[5]
        
        cursor.execute(
            """UPDATE expenses 
               SET date=%s, category=%s, amount=%s, description=%s 
               WHERE id=%s AND user_id=%s""",
            (new_date, new_category, new_amount, new_description, exp_id, user_id)
        )
        conn.commit()
        print("✅ Expense updated successfully!")
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()

def delete_expense(conn, user_id):
    """Delete an expense"""
    cursor = conn.cursor()
    
    view_expenses(conn, user_id)
    
    try:
        exp_id = int(input("\nEnter Expense ID to delete: "))
        
        cursor.execute(
            "SELECT * FROM expenses WHERE id=%s AND user_id=%s",
            (exp_id, user_id)
        )
        expense = cursor.fetchone()
        
        if not expense:
            print("❌ Expense not found or doesn't belong to you!")
            return
        
        confirm = input(f"Delete expense: {expense[3]} - ₹{expense[4]} - {expense[5]}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute(
                "DELETE FROM expenses WHERE id=%s AND user_id=%s",
                (exp_id, user_id)
            )
            conn.commit()
            print("✅ Expense deleted successfully!")
        else:
            print("❌ Deletion cancelled")
            
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()

# ============================================================================
# INCOME MANAGEMENT
# ============================================================================
def add_income(conn, user_id):
    """Add a new income record"""
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*50)
        print("➕ ADD INCOME")
        print("="*50)
        
        date_input = input("Date (YYYY-MM-DD) or press Enter for today: ").strip()
        if not date_input:
            date = datetime.now().strftime("%Y-%m-%d")
        else:
            datetime.strptime(date_input, "%Y-%m-%d")
            date = date_input
        
        amount = float(input("Income Amount: "))
        description = input("Description: ").strip()
        
        if amount <= 0:
            print("❌ Amount must be positive!")
            return
        
        cursor.execute(
            "INSERT INTO income (user_id, date, amount, description) VALUES (%s, %s, %s, %s)",
            (user_id, date, amount, description)
        )
        conn.commit()
        print("✅ Income added successfully!")
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()

def view_income(conn, user_id):
    """Display all income records"""
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, date, amount, description FROM income WHERE user_id=%s ORDER BY date DESC",
        (user_id,)
    )
    incomes = cursor.fetchall()
    cursor.close()
    
    if not incomes:
        print("\n📭 No income records found")
        return
    
    print("\n" + "="*70)
    print(f"{'ID':<5} {'Date':<12} {'Amount':<10} {'Description':<30}")
    print("="*70)
    for inc in incomes:
        print(f"{inc[0]:<5} {str(inc[1]):<12} ₹{inc[2]:<9.2f} {inc[3]:<30}")
    print("="*70)

def edit_income(conn, user_id):
    """Edit an existing income record"""
    cursor = conn.cursor()
    
    view_income(conn, user_id)
    
    try:
        inc_id = int(input("\nEnter Income ID to edit: "))
        
        cursor.execute(
            "SELECT * FROM income WHERE id=%s AND user_id=%s",
            (inc_id, user_id)
        )
        income = cursor.fetchone()
        
        if not income:
            print("❌ Income not found or doesn't belong to you!")
            return
        
        print(f"\nCurrent: Date={income[2]}, Amount=₹{income[3]}, Description={income[4]}")
        print("Press Enter to keep current value\n")
        
        new_date = input(f"New Date (current: {income[2]}): ").strip()
        if new_date:
            datetime.strptime(new_date, "%Y-%m-%d")
        else:
            new_date = income[2]
        
        new_amount = input(f"New Amount (current: {income[3]}): ").strip()
        if new_amount:
            new_amount = float(new_amount)
            if new_amount <= 0:
                print("❌ Amount must be positive!")
                return
        else:
            new_amount = income[3]
        
        new_description = input(f"New Description (current: {income[4]}): ").strip()
        new_description = new_description if new_description else income[4]
        
        cursor.execute(
            """UPDATE income 
               SET date=%s, amount=%s, description=%s 
               WHERE id=%s AND user_id=%s""",
            (new_date, new_amount, new_description, inc_id, user_id)
        )
        conn.commit()
        print("✅ Income updated successfully!")
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()

def delete_income(conn, user_id):
    """Delete an income record"""
    cursor = conn.cursor()
    
    view_income(conn, user_id)
    
    try:
        inc_id = int(input("\nEnter Income ID to delete: "))
        
        cursor.execute(
            "SELECT * FROM income WHERE id=%s AND user_id=%s",
            (inc_id, user_id)
        )
        income = cursor.fetchone()
        
        if not income:
            print("❌ Income not found or doesn't belong to you!")
            return
        
        confirm = input(f"Delete income: ₹{income[3]} - {income[4]}? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            cursor.execute(
                "DELETE FROM income WHERE id=%s AND user_id=%s",
                (inc_id, user_id)
            )
            conn.commit()
            print("✅ Income deleted successfully!")
        else:
            print("❌ Deletion cancelled")
            
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
    except mysql.connector.Error as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()

# ============================================================================
# AI INSIGHTS USING GEMINI
# ============================================================================
def get_ai_insights(conn,user_id,monthly_budget):
    expenses_df,income_df=load_user_data(conn,user_id)
    if expenses_df.empty:
        print("📭 No expenses found. Add some expenses first.")
        return
    # print("Available models:")
    # for m in genai.list_models():
    #     if 'generateContent' in m.supported_generation_methods:
    #         print(f"  - {m.name}")
    print("\n" + "="*50)
    print("🤖 AI FINANCIAL INSIGHTS")
    print("="*50)
    expenses_df=expenses_df.sort_values("date",ascending=False).head(30)
    # converting expenses into readable text for AI
    expenses_text=""
    for _,row in expenses_df.iterrows():
        expenses_text+=(
            f"Date : {row['date']},"
            f"Category : {row['category']},"
            f"Amount : {row['amount']},"
            f"Description : {row['description']},"
        )
    # AI prompt
    prompt = f"""
    You are a personal finance advisor.

    Monthly budget: ₹{monthly_budget}

    Below are the user's recent expenses.

    Tasks:
    1. Identify unnecessary or avoidable expenses.
    2. Explain why they are unnecessary.
    3. Suggest 3 clear ways to increase savings.

    Keep the advice short, practical, and beginner-friendly.

    Expenses:
    {expenses_text}
    """
    #Calling Gemini
    try:
        model=genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        print("\n" + response.text)
        print("\n" + "="*50)
    except Exception as e:
        print("❌ Error while calling Gemini AI")
        print(e)

# ============================================================================
# ANALYTICS & REPORTING
# ============================================================================
def load_user_data(conn, user_id):
    """Load user's expenses and income into pandas DataFrames"""
    expenses = pd.read_sql(
        "SELECT * FROM expenses WHERE user_id=%s",
        conn,
        params=(user_id,)
    )
    income = pd.read_sql(
        "SELECT * FROM income WHERE user_id=%s",
        conn,
        params=(user_id,)
    )
    return expenses, income

def show_summary(conn, user_id, monthly_budget):
    """Display financial summary"""
    expenses_df, income_df = load_user_data(conn, user_id)
    
    total_expense = expenses_df["amount"].sum() if not expenses_df.empty else 0
    total_income = income_df["amount"].sum() if not income_df.empty else 0
    savings = total_income - total_expense
    
    print("\n" + "="*50)
    print("💰 FINANCIAL SUMMARY")
    print("="*50)
    print(f"💵 Total Income:    ₹{total_income:,.2f}")
    print(f"💸 Total Expenses:  ₹{total_expense:,.2f}")
    print(f"💰 Net Savings:     ₹{savings:,.2f}")
    print(f"📊 Monthly Budget:  ₹{monthly_budget:,.2f}")
    
    if monthly_budget > 0:
        monthly_budget = float(monthly_budget)
        percent_used = (total_expense/monthly_budget) * 100
        print(f"📈 Budget Used:     {percent_used:.1f}%")
    
    print("="*50)
    
    # Budget alerts
    if total_expense > monthly_budget:
        print(f"⚠️  ALERT: Monthly budget exceeded by ₹{total_expense - monthly_budget:,.2f}")
    elif total_expense > monthly_budget * 0.8:
        print(f"⚠️  WARNING: You've used {(total_expense/monthly_budget)*100:.1f}% of your budget")
    else:
        print(f"✅ You're within budget! ₹{monthly_budget - total_expense:,.2f} remaining")
    print()

def show_charts(conn, user_id):
    """Display expense visualizations"""
    expenses_df, income_df = load_user_data(conn, user_id)
    
    if expenses_df.empty:
        print("\n📭 No expenses to visualize")
        return
    
    # Expenses by category
    category_exp = expenses_df.groupby("category")["amount"].sum().sort_values(ascending=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(x=category_exp.values, y=category_exp.index, palette="viridis",legend=False,hue=category_exp.index)
    plt.title("Expenses by Category", fontsize=16, fontweight='bold')
    plt.xlabel("Amount (₹)", fontsize=12)
    plt.ylabel("Category", fontsize=12)
    plt.tight_layout()
    plt.show()
    
    # Monthly expense trend
    expenses_df['month'] = pd.to_datetime(expenses_df['date']).dt.strftime("%Y-%m")
    monthly_exp = expenses_df.groupby("month")["amount"].sum()
    
    plt.figure(figsize=(10, 6))
    plt.plot(monthly_exp.index, monthly_exp.values, marker="o", linewidth=2, markersize=8)
    plt.title("Monthly Expense Trend", fontsize=16, fontweight='bold')
    plt.xlabel("Month", fontsize=12)
    plt.ylabel("Amount (₹)", fontsize=12)
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()
    
    # Income vs Expense comparison
    if not income_df.empty:
        income_df['month'] = pd.to_datetime(income_df['date']).dt.strftime("%Y-%m")
        monthly_inc = income_df.groupby("month")["amount"].sum()
        
        all_months = sorted(set(monthly_exp.index) | set(monthly_inc.index))
        exp_aligned = [monthly_exp.get(m, 0) for m in all_months]
        inc_aligned = [monthly_inc.get(m, 0) for m in all_months]
        
        plt.figure(figsize=(10, 6))
        x = np.arange(len(all_months))
        width = 0.35
        plt.bar(x - width/2, inc_aligned, width, label='Income', color='green', alpha=0.7)
        plt.bar(x + width/2, exp_aligned, width, label='Expenses', color='red', alpha=0.7)
        plt.xlabel('Month', fontsize=12)
        plt.ylabel('Amount (₹)', fontsize=12)
        plt.title('Income vs Expenses', fontsize=16, fontweight='bold')
        plt.xticks(x, all_months, rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()

# ============================================================================
# MAIN MENU
# ============================================================================
def display_menu():
    """Display the main menu"""
    print("\n" + "="*50)
    print("💼 EXPENSE TRACKER - MAIN MENU")
    print("="*50)
    print("1.  ➕ Add Expense")
    print("2.  ➕ Add Income")
    print("3.  📋 View All Expenses")
    print("4.  📋 View All Income")
    print("5.  ✏️  Edit Expense")
    print("6.  ✏️  Edit Income")
    print("7.  🗑️  Delete Expense")
    print("8.  🗑️  Delete Income")
    print("9.  💰 View Summary & Savings")
    print("10. 📊 Show Charts")
    print("11. 🤖 AI Insights (Smart Suggestions)")
    print("12. 🚪 Exit")
    print("="*50)

def main_menu(conn, user_id, monthly_budget):
    """Main application loop"""
    while True:
        display_menu()
        choice = input("Choose option (1-12): ").strip()
        
        if choice == "1":
            add_expense(conn, user_id)
        elif choice == "2":
            add_income(conn, user_id)
        elif choice == "3":
            view_expenses(conn, user_id)
        elif choice == "4":
            view_income(conn, user_id)
        elif choice == "5":
            edit_expense(conn, user_id)
        elif choice == "6":
            edit_income(conn, user_id)
        elif choice == "7":
            delete_expense(conn, user_id)
        elif choice == "8":
            delete_income(conn, user_id)
        elif choice == "9":
            show_summary(conn, user_id, monthly_budget)
        elif choice == "10":
            show_charts(conn, user_id)
        elif  choice == "11":
            get_ai_insights(conn,user_id,monthly_budget)
        elif choice == "12":
            print("\n👋 Thank you for using Expense Tracker!")
            print("💾 Closing database connection...")
            conn.close()
            print("✅ Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please select 1-11")

# ============================================================================
# MAIN PROGRAM
# ============================================================================
def main():
    """Main entry point of the application"""
    print("\n" + "="*50)
    print("💰 EXPENSE TRACKER APPLICATION")
    print("="*50)
    
    # Create database connection
    conn = create_connection()
    
    # Create tables if they don't exist
    create_tables(conn)
    
    # Login/Signup flow
    print("\n1. Sign Up (New User)")
    print("2. Login (Existing User)")
    choice = input("\nChoose option: ").strip()
    
    if choice == "1":
        signup(conn)
    
    # Login
    user_id, monthly_budget = login(conn)
    
    if user_id is None:
        print("❌ Login failed! Exiting...")
        conn.close()
        sys.exit(1)
    
    # Start main menu
    main_menu(conn, user_id, monthly_budget)

# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":

    main()

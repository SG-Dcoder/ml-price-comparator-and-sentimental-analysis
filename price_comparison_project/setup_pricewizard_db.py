# setup_pricewizard_db.py
import pymysql
import getpass

def setup_pricewizard_db():
    # Get root password
    root_password = getpass.getpass("Enter MySQL root password: ")
    
    # Connect to MySQL as root
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password=root_password
        )
        
        print("Connected to MySQL server successfully!")
        
        # Create cursor
        with conn.cursor() as cursor:
            # Create new database
            cursor.execute("CREATE DATABASE IF NOT EXISTS pricewizard")
            print("Database 'pricewizard' created successfully")
            
            # Create user if it doesn't exist and grant privileges
            try:
                # Set a password for wizard_user
                new_password = "wizard123"  # You can change this to a more secure password
                
                # Check if user exists
                cursor.execute("SELECT 1 FROM mysql.user WHERE user = 'wizard_user' AND host = 'localhost'")
                user_exists = cursor.fetchone()
                
                if user_exists:
                    # Update user password
                    cursor.execute(f"ALTER USER 'wizard_user'@'localhost' IDENTIFIED BY '{new_password}'")
                    print("User 'wizard_user' password updated")
                else:
                    # Create user
                    cursor.execute(f"CREATE USER 'wizard_user'@'localhost' IDENTIFIED BY '{new_password}'")
                    print("User 'wizard_user' created")
                
                # Grant privileges
                cursor.execute("GRANT ALL PRIVILEGES ON pricewizard.* TO 'wizard_user'@'localhost'")
                cursor.execute("FLUSH PRIVILEGES")
                print("Privileges granted to 'wizard_user'")
                
                print("\n--- Database Setup Complete ---")
                print(f"Database: pricewizard")
                print(f"Username: wizard_user")
                print(f"Password: {new_password}")
                print("\nPlease update your connection string with these credentials.")
                
            except pymysql.Error as e:
                print(f"Error creating user: {e}")
        
        conn.commit()
        
    except pymysql.Error as e:
        print(f"Error connecting to MySQL: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    setup_pricewizard_db()
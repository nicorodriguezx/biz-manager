# Sales Management System

A comprehensive web application built with Flask for managing sales, commissions, and transactions with an intuitive dashboard interface.

## Description

This project is a web application built using Flask that allows users to manage sales, commissions, and transactions. It provides a dashboard for users to view their daily summaries, sales reports, and manage products. The application also includes an admin interface for managing users and expenses.

## Features

- 🔐 User authentication and authorization using Flask-Login
- 📊 Daily sales summary with commission calculations
- 📝 Transaction logging for extracts and returns
- 📱 Responsive design with a modern UI using CSS
- 👑 Admin dashboard for managing users, products, and expenses
- 💾 Data stored in JSON files for easy access and manipulation

## Technologies Used

- **Backend:** Flask
- **Frontend:** HTML, CSS, JavaScript
- **Database:** JSON files for data storage

### Dependencies

- Flask==3.1.0
- Flask-Login==0.6.3
- Additional dependencies can be found in `requirements.txt`

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sales-management-system.git
   cd sales-management-system
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:

   **Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

5. Set up environment variables:
   - Create a `.env` file in the root directory
   - Add your secret key:
   ```bash
   SECRET_KEY=your_secret_key_here
   ```

6. Run the application:
   ```bash
   flask run
   ```

7. Open your browser and go to `http://127.0.0.1:5000`

## Default Login

The application comes with a default admin account:
- Username: `a`
- Password: `a`

> **Note:** It is highly recommended to change these credentials after your first login for security purposes.

## Usage

### Admin Dashboard
- Manage user accounts
- View comprehensive sales reports
- Handle system expenses
- Product management

### Vendor User Dashboard
- View daily sales summary
- Manage transactions
- Track commissions
- Handle product sales

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the Flask community for their support and documentation
- Icons used in the project are from Font Awesome
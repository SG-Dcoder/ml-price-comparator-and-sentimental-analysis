# ml-price-comparator-and-sentimental-analysis
Price Comparison Tool
A web application that compares product prices across Amazon and Flipkart, providing price forecasting and platform reliability analysis.

Features
Search products across multiple e-commerce platforms (Amazon, Flipkart)
Compare prices to find the best deals
View product ratings and reviews
Analyze platform reliability based on sentiment analysis
Price forecasting to determine the best time to buy
Price history tracking
Tech Stack
Backend: Python, Flask
Frontend: HTML, CSS, JavaScript, Bootstrap
Data Analysis: Pandas, NumPy, Matplotlib
Machine Learning: Scikit-learn
Web Scraping: BeautifulSoup, Requests
Installation
Prerequisites
Python 3.8 or higher
pip (Python package manager)
Git
Step 1: Clone the Repository
bash


git clone https://github.com/yourusername/price-comparison-tool.git
cd price-comparison-tool
Step 2: Create a Virtual Environment
bash


# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
Step 3: Install Dependencies
bash


pip install -r requirements.txt
Step 4: Create Required Directories
bash


mkdir -p data/price_history data/reviews
Usage
Running the Application
bash


python app.py
The application will start running on http://127.0.0.1:5000

How to Use
Open your web browser and navigate to http://127.0.0.1:5000
Enter a product name in the search box (e.g., "smartphone", "laptop", etc.)
View the comparison results, including:
Products from different platforms
Price comparisons
Best deal recommendation
Platform reliability analysis
Price forecast (if historical data is available)

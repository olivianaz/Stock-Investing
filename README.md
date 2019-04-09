# Stock-Investing
Stock-Investing is a tool to help decide which covered call options might be profitable to open in the short term.

## Getting Started
This project is written in Python 3. It requires the numpy, pandas, and beautiful soup 4 libraries. You can use pip to install these libraries if you haven't already.
<br>`pip install numpy`
<br>`pip install pandas`
<br>`pip install beautifulsoup4`
<br>It also requires Jupyter. Please see the following for details on getting up and running with Jupyter notebook: https://jupyter.org/install

Once Jupyter and all the needed libraries are installed, run the following:
* jupyter notebook: this would open a tab in your browser for jupyter notebook
* navigate to Scrape Options Data.ipynb and open it
* click Run All from the menu and it will extract option and stock pricing for the sample stock tickers in the notebook and provide the results in the last notebook cell
* you can update the line `ticker_list = ...` to include the list of ticker symbols that you're interested in and re-run.

## License

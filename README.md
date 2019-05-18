# Stock-Investing
Stock-Investing is a tool to help decide which covered call options might be profitable to open in the short term.

## Getting Started
This project is written in Python 3. It requires the _numpy_, _pandas_, and _beautiful soup 4_ libraries. You can use pip to install these libraries if you haven't already.
```pip install numpy
pip install pandas
pip install beautifulsoup4
```

It also requires Jupyter. Please see this [link](https://jupyter.org/install) for details on getting up and running with Jupyter notebook.

Once Jupyter and all the needed libraries are installed, do the following:
* run `jupyter notebook` from the terminal: this would open a tab in your browser for jupyter notebook
* navigate to _Scrape Options Data.ipynb_ and open it
* click _Run All_ from the menu and it will extract option and stock pricing for the sample stock tickers in the notebook and provide the results in the last notebook cell
* you can update the line `ticker_list = ...` to include the list of ticker symbols that you're interested in and re-run all the cells in the notebook.

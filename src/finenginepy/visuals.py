import matplotlib.pyplot as plt
import pandas as pd

def plot_financials(clean_data, ticker):
    print(f"\n[+] Generating financial charts for {ticker}...")
    
    # We drop the 2021 row since it has NaN values, leaving us with clean plottable data
    plot_data = clean_data.dropna()
    
    # Set up the canvas
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Extract the dates (e.g., '2022-09-30') for our x-axis labels
    dates = [str(d).split(' ')[0] for d in plot_data.index]
    
    # Math to place two bars side-by-side for each year
    x = range(len(dates))
    width = 0.35
    
    # Plot Revenue (Blue) and FCF (Green) scaled to Billions
    ax.bar([i - width/2 for i in x], plot_data['Revenue'] / 1e9, width, label='Revenue', color='#1f77b4')
    ax.bar([i + width/2 for i in x], plot_data['Free Cash Flow'] / 1e9, width, label='Free Cash Flow', color='#2ca02c')
    
    # Formatting the chart
    ax.set_ylabel('Billions (USD)')
    ax.set_title(f'{ticker} Historical Revenue vs. Free Cash Flow')
    ax.set_xticks(x)
    ax.set_xticklabels(dates)
    ax.legend()
    
    # Save the chart as an image file in your main folder
    chart_filename = f"{ticker}_financials.png"
    plt.savefig(chart_filename, dpi=300, bbox_inches='tight')
    print(f"Chart successfully saved as: {chart_filename}")
    
    # Pop the chart open on your screen
    plt.show()

if __name__ == "__main__":
    from data_fetcher import fetch_raw_data, clean_financials
    
    inc, bal, cf, info = fetch_raw_data("AAPL")
    clean_data = clean_financials(inc, bal, cf)
    plot_financials(clean_data, "AAPL")
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from plot_utils import plot_city_trends, complete_timeseries_data

def load_data():
    # Load the consolidated song velocity table
    return pd.read_csv('data/song_velocity_table.csv')

def analyze_peaks():
    # Load the data
    df = load_data()
    
    # Separate streams and listeners data
    streams_data = df[df['Measure'].str.lower() == 'plays'].copy()
    listeners_data = df[df['Measure'].str.lower() == 'listeners'].copy()
    
    # Calculate peaks by city
    city_peaks = pd.DataFrame()
    
    for city in df['City'].unique():
        city_streams = streams_data[streams_data['City'] == city]
        city_listeners = listeners_data[listeners_data['City'] == city]
        
        peak_streams = city_streams['Current Period'].max() if not city_streams.empty else 0
        peak_listeners = city_listeners['Current Period'].max() if not city_listeners.empty else 0
        
        peak_streams_week = city_streams.loc[city_streams['Current Period'].idxmax()]['Week'] if not city_streams.empty else None
        peak_listeners_week = city_listeners.loc[city_listeners['Current Period'].idxmax()]['Week'] if not city_listeners.empty else None
        
        city_peaks = pd.concat([city_peaks, pd.DataFrame({
            'City': [city],
            'Peak Streams': [peak_streams],
            'Peak Streams Week': [peak_streams_week],
            'Peak Listeners': [peak_listeners],
            'Peak Listeners Week': [peak_listeners_week]
        })], ignore_index=True)
    
    # Sort by peak streams
    city_peaks = city_peaks.sort_values('Peak Streams', ascending=False)
    
    # Plot top 10 cities peaks
    top_10_cities = city_peaks.head(10)
    
    # Create a bar plot for peaks
    plt.figure(figsize=(15, 8))
    
    x = range(len(top_10_cities))
    width = 0.35
    
    plt.bar(x, top_10_cities['Peak Streams'], width, label='Peak Streams', color='skyblue')
    plt.bar([i + width for i in x], top_10_cities['Peak Listeners'], width, label='Peak Listeners', color='lightgreen')
    
    plt.xlabel('Cities')
    plt.ylabel('Count')
    plt.title('Peak Streams and Listeners by City (Top 10)')
    plt.xticks([i + width/2 for i in x], top_10_cities['City'], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.show()
    
    # Plot trend lines for top 5 cities
    top_5_cities = top_10_cities['City'].head().tolist()
    
    # Streams trends
    streams_trend_data = streams_data[streams_data['City'].isin(top_5_cities)].copy()
    streams_trend_data = complete_timeseries_data(
        data=streams_trend_data,
        date_column='Week',
        value_columns='Current Period',
        grouping_columns=['City', 'Song']
    )
    
    plot_city_trends(
        data=streams_trend_data,
        y_column='Current Period',
        title='Streams Over Time in Top 5 Cities',
        y_label='Weekly Streams',
        cities=top_5_cities,
        date_column='Week',
        city_column='City',
        song_column='Song'
    )
    
    # Listeners trends
    listeners_trend_data = listeners_data[listeners_data['City'].isin(top_5_cities)].copy()
    listeners_trend_data = complete_timeseries_data(
        data=listeners_trend_data,
        date_column='Week',
        value_columns='Current Period',
        grouping_columns=['City', 'Song']
    )
    
    plot_city_trends(
        data=listeners_trend_data,
        y_column='Current Period',
        title='Listeners Over Time in Top 5 Cities',
        y_label='Weekly Listeners',
        cities=top_5_cities,
        date_column='Week',
        city_column='City',
        song_column='Song'
    )
    
    # Print summary statistics
    print("\nPeak Performance Summary for Top 10 Cities:")
    print("=" * 80)
    for _, row in top_10_cities.iterrows():
        print(f"\nCity: {row['City']}")
        print(f"Peak Streams: {row['Peak Streams']} (Week of {row['Peak Streams Week']})")
        print(f"Peak Listeners: {row['Peak Listeners']} (Week of {row['Peak Listeners Week']})")

if __name__ == "__main__":
    analyze_peaks() 
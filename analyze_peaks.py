import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from plot_utils import plot_city_trends, complete_timeseries_data
from datetime import datetime
from config import songs_to_scrape

def load_data():
    """Load the consolidated song velocity table."""
    return pd.read_csv('song_velocity_table.csv')

def get_song_release_date(song_id):
    """Get the release date for a song from config."""
    # Convert song_id to string for comparison
    song_id = str(song_id)
    # print(f"\nDebug - Looking for song ID: {song_id}")
    # print(f"Debug - Type of input song_id: {type(song_id)}")
    # print(f"Debug - Available songs in config:")
    for song in songs_to_scrape:
        # print(f"  - {song['name']}: {song['id']} (release: {song['release_date']})")
        # print(f"    Comparing '{song['id']}' ({type(song['id'])}) with '{song_id}' ({type(song_id)})")
        if song['id'] == song_id:
            # print(f"    ✓ Found match!")
            return datetime.strptime(song['release_date'], '%Y%m%d')
        # else:
        #     print(f"    ✗ No match")
    # print("  ❌ No match found")
    return None

def calculate_city_peak_metrics(df):
    """
    Calculate city-level peak metrics including average time to peak, peak streams, and peak listeners.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the song velocity data
    
    Returns:
    --------
    tuple
        (city_metrics, song_metrics) where:
        - city_metrics: DataFrame with aggregated city-level metrics
        - song_metrics: DataFrame with individual song-level metrics
    """
    # Ensure all column names are lowercase
    df.columns = df.columns.str.lower()
    
    # Filter for weekly data only
    df = df[df['period_type'].str.lower() == 'weekly'].copy()
    
    # Separate streams and listeners data, excluding "All Cities" and artist level
    streams_data = df[
        (df['measure'].str.lower() == 'plays') & 
        (df['city'].str.lower() != 'all cities') &
        (~df['song'].str.lower().str.contains('artist level', case=False, na=False))
    ].copy()
    
    listeners_data = df[
        (df['measure'].str.lower() == 'listeners') & 
        (df['city'].str.lower() != 'all cities') &
        (~df['song'].str.lower().str.contains('artist level', case=False, na=False))
    ].copy()
    
    print("\nDebug - Available songs in streams data:")
    print(streams_data['song'].unique())
    print("\nDebug - Available songs in listeners data:")
    print(listeners_data['song'].unique())
    
    # Initialize results lists
    city_metrics_list = []
    song_metrics_list = []
    
    for city in df['city'].unique():
        if city == 'All Cities':  # Skip aggregate data
            continue
            
        # Get city-specific data
        city_streams = streams_data[streams_data['city'] == city]
        city_listeners = listeners_data[listeners_data['city'] == city]
        
        print(f"\nDebug - Processing city: {city}")
        print(f"Debug - Number of songs in streams: {len(city_streams['song'].unique())}")
        print(f"Debug - Number of songs in listeners: {len(city_listeners['song'].unique())}")
        
        # Calculate time to peak for each song in the city
        time_to_peak_list = []
        first_week_peaks = 0
        total_songs = 0
        missing_release_date = 0
        still_growing = 0
        
        for song in city_streams['song'].unique():
            # Create a proper copy of the song data
            song_data = city_streams[city_streams['song'] == song].copy()
            if not song_data.empty:
                total_songs += 1
                
                # Get song ID from the data
                song_id = song_data['song_id'].iloc[0]
                # Get release date from config
                release_date = get_song_release_date(song_id)
                if release_date is None:
                    missing_release_date += 1
                    continue
                
                # Convert week column to datetime properly
                song_data = song_data.assign(week=pd.to_datetime(song_data['week'], format='%Y%m%d'))
                    
                # Get peak date and streams
                peak_date = song_data.loc[song_data['current_period'].idxmax()]['week']
                peak_streams = song_data['current_period'].max()
                
                # Check if the song is still growing (peak is in the most recent week)
                latest_week = song_data['week'].max()
                is_still_growing = peak_date == latest_week
                
                # Calculate weeks to peak
                weeks_to_peak = (peak_date - release_date).days / 7 if not is_still_growing else None
                
                # Get listener data for this song
                print(f"\nDebug - Looking for listener data for song: {song}")
                print(f"Debug - Available listener songs in city:")
                print(city_listeners['song'].unique())
                
                # Try to find the corresponding artist level entry
                artist_name = song.split(' - ')[0] if ' - ' in song else song
                song_listener_data = city_listeners[city_listeners['song'].str.contains(artist_name, case=False, na=False)]
                
                print(f"Debug - Found listener data: {not song_listener_data.empty}")
                if not song_listener_data.empty:
                    print(f"Debug - Listener data song name: {song_listener_data['song'].iloc[0]}")
                
                peak_listeners = song_listener_data['current_period'].max() if not song_listener_data.empty else 0
                
                # Add to song metrics list
                song_metrics_list.append({
                    'city': city,
                    'song': song,
                    'song_id': song_id,
                    'release_date': release_date.strftime('%Y-%m-%d'),
                    'peak_date': peak_date.strftime('%Y-%m-%d'),
                    'peak_streams': peak_streams,
                    'peak_listeners': peak_listeners,
                    'weeks_to_peak': round(weeks_to_peak, 1) if weeks_to_peak is not None else None,
                    'is_still_growing': is_still_growing,
                    'peaked_first_week': weeks_to_peak == 0 if weeks_to_peak is not None else False
                })
                
                if is_still_growing:
                    still_growing += 1
                elif weeks_to_peak == 0:  # Song peaked in first week
                    first_week_peaks += 1
                    time_to_peak_list.append(0)
                elif weeks_to_peak is not None and weeks_to_peak > 0:  # Only include valid time differences
                    time_to_peak_list.append(weeks_to_peak)
        
        # Calculate average time to peak
        avg_time_to_peak = sum(time_to_peak_list) / len(time_to_peak_list) if time_to_peak_list else None
        avg_weeks_to_peak = round(avg_time_to_peak, 1) if avg_time_to_peak is not None else None
        
        # Calculate peak streams (across all songs)
        peak_streams = city_streams['current_period'].max() if not city_streams.empty else 0
        
        # Calculate peak listeners (at artist level)
        peak_listeners = city_listeners['current_period'].max() if not city_listeners.empty else 0
        
        # Add to city metrics list
        city_metrics_list.append({
            'city': city,
            'avg_weeks_to_peak': avg_weeks_to_peak,
            'peak_streams': peak_streams,
            'peak_listeners': peak_listeners,
            'songs_analyzed': total_songs,
            'songs_peaked_first_week': first_week_peaks,
            'pct_peaked_first_week': round((first_week_peaks / total_songs * 100) if total_songs > 0 else 0, 1),
            'songs_missing_release_date': missing_release_date,
            'songs_still_growing': still_growing
        })
    
    # Create DataFrames from lists
    city_metrics = pd.DataFrame(city_metrics_list)
    song_metrics = pd.DataFrame(song_metrics_list)
    
    # Sort city metrics by peak streams in descending order
    city_metrics = city_metrics.sort_values('peak_streams', ascending=False)
    
    return city_metrics, song_metrics

def export_peak_metrics(city_metrics, song_metrics, output_dir='analysis_outputs'):
    """
    Export city and song peak metrics to CSV files.
    
    Parameters:
    -----------
    city_metrics : pd.DataFrame
        DataFrame containing city peak metrics
    song_metrics : pd.DataFrame
        DataFrame containing song-level metrics
    output_dir : str
        Directory to save the output files
    """
    # Create timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create directory if it doesn't exist
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    # Export city metrics
    city_filename = f'{output_dir}/city_peak_metrics_{timestamp}.csv'
    city_metrics.to_csv(city_filename, index=False)
    print(f"\nCity peak metrics exported to: {city_filename}")
    
    # Export song metrics
    song_filename = f'{output_dir}/song_peak_metrics_{timestamp}.csv'
    song_metrics.to_csv(song_filename, index=False)
    print(f"Song peak metrics exported to: {song_filename}")

def analyze_peaks(df=None, export_results=True):
    """
    Analyze and visualize peak metrics for cities.
    
    Parameters:
    -----------
    df : pd.DataFrame, optional
        DataFrame containing the song velocity data. If None, data will be loaded from file.
    export_results : bool
        Whether to export results to CSV
    """
    # Load the data if not provided
    if df is None:
        df = load_data()
    
    # Calculate city peak metrics and song metrics
    city_metrics, song_metrics = calculate_city_peak_metrics(df)
    
    # Print the results
    print("\nCity Peak Metrics Summary:")
    print("=" * 80)
    print(city_metrics.to_string(index=False))
    
    # Print interpretation of metrics
    print("\nInterpretation Notes:")
    print("- avg_weeks_to_peak: Average weeks from release to peak streams")
    print("  - 0 means the song peaked in its first week")
    print("  - None means no valid time-to-peak data was available, which could be due to:")
    print("    * Song is still growing (peak is in most recent week)")
    print("    * Song data is incomplete")
    print("- songs_peaked_first_week: Number of songs that peaked in their first week")
    print("- pct_peaked_first_week: Percentage of songs that peaked in their first week")
    print("- songs_missing_release_date: Number of songs where release date wasn't found")
    print("- songs_still_growing: Number of songs that haven't peaked yet (peak is in most recent week)")
    
    # Export results if requested
    if export_results:
        export_peak_metrics(city_metrics, song_metrics)
    
    # Plot top 10 cities peaks
    top_10_cities = city_metrics.head(10)
    
    # Create a bar plot for peaks
    plt.figure(figsize=(15, 8))
    
    x = range(len(top_10_cities))
    width = 0.35
    
    plt.bar(x, top_10_cities['peak_streams'], width, label='Peak Streams', color='skyblue')
    plt.bar([i + width for i in x], top_10_cities['peak_listeners'], width, label='Peak Listeners', color='lightgreen')
    
    plt.xlabel('Cities')
    plt.ylabel('Count')
    plt.title('Peak Streams and Listeners by City (Top 10)')
    plt.xticks([i + width/2 for i in x], top_10_cities['city'], rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Example usage
    df = load_data()
    city_metrics, song_metrics = calculate_city_peak_metrics(df)
    
    # Print city metrics
    print("\nCity Peak Metrics:")
    print("=" * 80)
    print(city_metrics.head())
    
    # Print song metrics
    print("\nSong Peak Metrics:")
    print("=" * 80)
    print(song_metrics.head())
    
    # Run full analysis
    analyze_peaks() 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from config import songs_to_scrape

# Import the analysis functions defined above
def analyze_song_popularity(df, measure='listeners', period_type='weekly', level='song', group_by='city'):
    """Analyze song popularity patterns following config structure"""
    
    # Group by song and week to get average streams
    weekly_stats = df.groupby(['Song', 'Week']).agg({
        'Current Period': ['mean', 'sum']
    }).reset_index()
    weekly_stats.columns = ['Song', 'Week', 'avg_streams', 'total_streams']
    
    # Find peak weeks for each song
    peak_stats = weekly_stats.sort_values('total_streams', ascending=False).groupby('Song').first()
    
    # Calculate time to peak (weeks from release)
    song_release_dates = {song['name']: song['release_date'] for song in songs_to_scrape}
    peak_stats['weeks_to_peak'] = peak_stats.apply(
        lambda x: (pd.to_datetime(x.name) - pd.to_datetime(song_release_dates[x.name])).days / 7,
        axis=1
    )
    
    # Calculate post-peak retention
    def get_retention(song_data):
        peak_week = song_data.loc[song_data['total_streams'].idxmax(), 'Week']
        post_peak = song_data[pd.to_datetime(song_data['Week']) > pd.to_datetime(peak_week)]
        return post_peak['total_streams'].mean() if len(post_peak) > 0 else 0
    
    retention_stats = weekly_stats.groupby('Song').apply(get_retention).to_frame('avg_post_peak')
    
    return {
        'peak_stats': peak_stats,
        'retention_stats': retention_stats
    }

def plot_song_popularity_analysis(df, output_path=None):
    """Create visualizations for song popularity analysis"""
    plt.style.use('seaborn')
    fig = plt.figure(figsize=(15, 10))
    
    # 1. Weekly Streams Over Time
    ax1 = plt.subplot(2, 2, 1)
    for song in df['Song'].unique():
        song_data = df[df['Song'] == song].sort_values('Week')
        plt.plot(pd.to_datetime(song_data['Week']), 
                song_data['Current Period'],
                label=song, marker='o')
    plt.title('Weekly Streams Over Time')
    plt.xticks(rotation=45)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    
    # 2. Peak Analysis
    ax2 = plt.subplot(2, 2, 2)
    peak_data = df.groupby('Song')['Current Period'].max().sort_values(ascending=True)
    peak_data.plot(kind='barh')
    plt.title('Peak Streams by Song')
    
    # 3. Geographic Heat Map
    ax3 = plt.subplot(2, 2, 3)
    city_data = df.groupby('City')['Current Period'].mean().sort_values(ascending=False)
    sns.heatmap(city_data.head(10).to_frame().T, cmap='YlOrRd')
    plt.title('Top 10 Cities by Average Streams')
    
    # 4. Retention Analysis
    ax4 = plt.subplot(2, 2, 4)
    for song in df['Song'].unique():
        song_data = df[df['Song'] == song].sort_values('Week')
        max_streams = song_data['Current Period'].max()
        if max_streams > 0:
            relative_streams = song_data['Current Period'] / max_streams
            plt.plot(range(len(relative_streams)), 
                    relative_streams,
                    label=song, marker='o')
    plt.title('Stream Retention (% of Peak)')
    plt.xlabel('Weeks from Release')
    plt.ylabel('% of Peak Streams')
    
    plt.tight_layout()
    
    if output_path:
        plt.savefig(output_path)
    
    return fig

if __name__ == "__main__":
    # Load the data
    df = pd.read_csv('song_velocity_table.csv')
    
    # Run analysis
    popularity_stats = analyze_song_popularity(df)
    
    # Create and save visualizations
    fig = plot_song_popularity_analysis(df, output_path='analysis_outputs/popularity_analysis.png')
    
    # Print summary statistics
    print("\nPopularity Analysis Summary:")
    print("-" * 50)
    print("\nPeak Statistics:")
    print(popularity_stats['peak_stats'])
    print("\nRetention Statistics:")
    print(popularity_stats['retention_stats'])
    
    plt.show() 
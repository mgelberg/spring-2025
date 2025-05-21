import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict
from datetime import datetime
import os

def load_data():
    """Load the consolidated song velocity table."""
    return pd.read_csv('data/song_velocity_table.csv')

def analyze_adoption_patterns(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Analyze adoption patterns for songs across cities.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing the song data with columns:
        - city: str
        - previous_period: float
        - current_period: float
        - %_change: float
        - week: datetime
        - song: str
        - song_id: str
        - measure: str ('plays' or 'listeners')
        - level: str
        - grouping: str
        - period_type: str
    
    Returns:
    --------
    Dict[str, pd.DataFrame]
        Dictionary containing:
        - 'city_adoption': Detailed adoption data for each city-song combination
        - 'city_summary': Summary metrics for each city
        - 'category_metrics': Summary metrics for each adoption category
    """
    # Filter out monthly and artist-level data
    df = df[~df['song'].str.contains('artist level', case=False, na=False)]
    df = df[df['grouping'] == 'city']
    
    # Convert week to datetime if not already
    df['week'] = pd.to_datetime(df['week'])
    
    # Initialize DataFrame to store city adoption metrics
    city_adoption = pd.DataFrame()
    
    # Get first activity date for each song (this will be treated as release date)
    song_release_dates = df[df['current_period'] > 0].groupby('song')['week'].min()
    
    print(f"\nAnalyzing {len(song_release_dates)} songs")
    print("\nSongs being analyzed:")
    for song in song_release_dates.index:
        print(f"- {song}")
    
    for city in df['city'].unique():
        if city == 'All Cities':  # Skip aggregate data
            continue
            
        city_data = df[df['city'] == city]
        
        # Analyze adoption for each song
        for song in df['song'].unique():
            song_city_data = city_data[city_data['song'] == song]
            
            if song_city_data.empty:
                continue
                
            release_date = song_release_dates[song]
            
            # Find first activity for this city and song
            song_city_activity = song_city_data[song_city_data['current_period'] > 0]
            if song_city_activity.empty:
                continue
                
            first_activity = song_city_activity['week'].min()
            last_activity = song_city_activity['week'].max()
            
            # Calculate weeks from release to first activity
            weeks_to_adopt = (first_activity - release_date).days / 7
            
            # Calculate active weeks and total weeks since adoption
            active_weeks = song_city_activity['week'].nunique()
            total_weeks = (last_activity - first_activity).days / 7 + 1 if first_activity else 0
            
            # Calculate engagement metrics
            total_streams = song_city_data[song_city_data['measure'].str.lower() == 'plays']['current_period'].sum()
            total_listeners = song_city_data[song_city_data['measure'].str.lower() == 'listeners']['current_period'].sum()
            
            # Calculate consistency score
            consistency = (active_weeks / total_weeks) * 100 if total_weeks > 0 else 0
            
            # Add to city_adoption DataFrame
            city_adoption = pd.concat([city_adoption, pd.DataFrame({
                'city': [city],
                'song': [song],
                'release_date': [release_date],
                'first_activity': [first_activity],
                'weeks_to_adopt': [weeks_to_adopt],
                'total_streams': [total_streams],
                'total_listeners': [total_listeners],
                'active_weeks': [active_weeks],
                'consistency_score': [consistency]
            })], ignore_index=True)
    
    # Calculate average adoption speed and consistency for each city across all songs
    city_summary = city_adoption.groupby('city').agg({
        'weeks_to_adopt': 'mean',
        'consistency_score': 'mean',
        'total_streams': 'sum',
        'total_listeners': 'sum',
        'song': 'count'  # Count how many songs each city engaged with
    }).reset_index()
    
    # Rename the song count column
    city_summary = city_summary.rename(columns={'song': 'songs_engaged'})
    
    # Categorize cities based on average adoption speed
    percentile_33 = city_summary['weeks_to_adopt'].quantile(0.33)
    percentile_67 = city_summary['weeks_to_adopt'].quantile(0.67)
    
    def categorize_city(row):
        if row['weeks_to_adopt'] <= percentile_33:
            return 'Early Adopter'
        elif row['weeks_to_adopt'] <= percentile_67:
            return 'Mid Adopter'
        else:
            return 'Late Bloomer'
    
    city_summary['category'] = city_summary.apply(categorize_city, axis=1)
    
    # Calculate category metrics
    category_metrics = city_summary.groupby('category').agg({
        'total_streams': 'mean',
        'total_listeners': 'mean',
        'consistency_score': 'mean',
        'weeks_to_adopt': 'mean',
        'songs_engaged': 'mean',
        'city': 'count'
    }).round(2)
    
    return {
        'city_adoption': city_adoption,
        'city_summary': city_summary,
        'category_metrics': category_metrics
    }

def export_adoption_results(results: Dict[str, pd.DataFrame], output_dir='analysis_outputs'):
    """
    Export adoption analysis results to CSV files.
    
    Parameters:
    -----------
    results : Dict[str, pd.DataFrame]
        Dictionary containing adoption analysis results
    output_dir : str
        Directory to save the output files
    """
    # Create timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Create directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Export each DataFrame
    for key, df in results.items():
        filename = f'{output_dir}/adoption_{key}_{timestamp}.csv'
        df.to_csv(filename, index=False)
        print(f"\nExported {key} data to: {filename}")

def display_adoption_results(results: Dict[str, pd.DataFrame]) -> None:
    """
    Display the results from analyze_adoption_patterns in a clear, formatted way.
    
    Parameters:
    -----------
    results : Dict[str, pd.DataFrame]
        Dictionary containing:
        - 'city_adoption': Detailed adoption data for each city-song combination
        - 'city_summary': Summary metrics for each city
        - 'category_metrics': Summary metrics for each adoption category
    """
    # Filter out cities with less than 100 lifetime streams
    city_summary = results['city_summary'][results['city_summary']['total_streams'] >= 50].copy()
    
    # Recalculate category metrics with filtered data
    category_metrics = city_summary.groupby('category').agg({
        'total_streams': 'mean',
        'total_listeners': 'mean',
        'consistency_score': 'mean',
        'weeks_to_adopt': 'mean',
        'songs_engaged': 'mean',
        'city': 'count'
    }).round(2)
    
    # 1. Display Metric Explanations
    print("\n=== Metric Explanations ===")
    print("\nConsistency Score:")
    print("• Calculated as: (Number of Active Weeks / Total Weeks Since First Activity) × 100")
    print("• Active Week: A week where the song had any streams")
    print("• Higher scores indicate more consistent engagement over time")
    print("• Example: A score of 75% means the city was active 75% of the weeks since they first played the song")
    
    print("\nWeeks to Adopt:")
    print("• Measures how quickly a city starts playing a song after its release")
    print("• Calculated as: (First Activity Date - Song Release Date) in weeks")
    print("• Lower numbers indicate faster adoption")
    print("• Example: 2.5 weeks means the city started playing the song 2.5 weeks after release")
    
    print("\nNote: Analysis excludes cities with fewer than 50 lifetime streams")
    
    # 2. Display Category Overview
    print("\n=== City Categories Overview ===")
    
    # Format the metrics for better readability
    formatted_metrics = category_metrics.copy()
    formatted_metrics['total_streams'] = formatted_metrics['total_streams'].apply(lambda x: f"{x:,.0f}")
    formatted_metrics['total_listeners'] = formatted_metrics['total_listeners'].apply(lambda x: f"{x:,.0f}")
    formatted_metrics['consistency_score'] = formatted_metrics['consistency_score'].apply(lambda x: f"{x:.1f}%")
    formatted_metrics['weeks_to_adopt'] = formatted_metrics['weeks_to_adopt'].apply(lambda x: f"{x:.1f}")
    formatted_metrics['songs_engaged'] = formatted_metrics['songs_engaged'].apply(lambda x: f"{x:.1f}")
    formatted_metrics['city'] = formatted_metrics['city'].apply(lambda x: f"{x:.0f}")
    
    print("\nCategory Statistics:")
    print(formatted_metrics)
    
    # 3. Display Top Cities by Category
    print("\n=== Top Cities by Category ===")
    
    for category in ['Early Adopter', 'Mid Adopter', 'Late Bloomer']:
        category_cities = city_summary[city_summary['category'] == category]
        top_cities = category_cities.nlargest(3, 'consistency_score')
        
        print(f"\nTop {category} Cities:")
        for _, city in top_cities.iterrows():
            print(f"- {city['city']}:")
            print(f"  • Consistency Score: {city['consistency_score']:.1f}%")
            print(f"  • Average Weeks to Adopt: {city['weeks_to_adopt']:.1f}")
            print(f"  • Total Songs Engaged: {city['songs_engaged']:.0f}")
            print(f"  • Total Streams: {city['total_streams']:,.0f}")
    
    # 4. Create visualizations
    plt.figure(figsize=(15, 10))
    
    # 4.1 Adoption Speed vs Consistency Plot
    plt.subplot(2, 1, 1)
    sns.scatterplot(data=city_summary, 
                    x='weeks_to_adopt',
                    y='consistency_score',
                    hue='category',
                    size='songs_engaged',
                    sizes=(50, 400),
                    alpha=0.6)
    
    plt.title('City Adoption Patterns: Speed vs Consistency\n(Cities with 50+ Streams)')
    plt.xlabel('Average Weeks Until First Activity')
    plt.ylabel('Consistency Score (%)')
    
    # Add city labels for points with high engagement
    for idx, row in city_summary[city_summary['songs_engaged'] >= city_summary['songs_engaged'].quantile(0.75)].iterrows():
        plt.annotate(row['city'], 
                    (row['weeks_to_adopt'], row['consistency_score']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8, alpha=0.7)
    
    # 4.2 Category Distribution Plot
    plt.subplot(2, 1, 2)
    category_counts = city_summary['category'].value_counts()
    sns.barplot(x=category_counts.index, y=category_counts.values)
    plt.title('Distribution of Cities Across Categories\n(Cities with 50+ Streams)')
    plt.xlabel('Category')
    plt.ylabel('Number of Cities')
    
    # Add value labels on top of bars
    for i, v in enumerate(category_counts.values):
        plt.text(i, v, str(v), ha='center', va='bottom')
    
    plt.tight_layout()
    plt.show()
    
    # 5. Display Song Adoption Stats
    print("\n=== Song Adoption Statistics ===")
    # Filter city_adoption to match filtered city_summary
    active_cities = city_summary['city'].unique()
    filtered_city_adoption = results['city_adoption'][
        results['city_adoption']['city'].isin(active_cities)
    ]
    
    song_stats = filtered_city_adoption.groupby('song').agg({
        'weeks_to_adopt': 'mean',
        'consistency_score': 'mean',
        'city': 'count'
    }).round(2)
    
    song_stats = song_stats.rename(columns={
        'weeks_to_adopt': 'avg_weeks_to_adopt',
        'consistency_score': 'avg_consistency',
        'city': 'num_cities'
    })
    
    # Sort by number of cities and average consistency
    top_songs = song_stats.sort_values(['num_cities', 'avg_consistency'], ascending=[False, False]).head(5)
    
    print("\nTop 5 Most Widely Adopted Songs (In Cities with 50+ Streams):")
    if not top_songs.empty:
        # Prepare DataFrame for table display
        display_top_songs = top_songs.copy()
        display_top_songs['avg_consistency'] = display_top_songs['avg_consistency'].apply(lambda x: f"{x:.1f}%")
        # Reset index to make 'song' a column for better display with to_string()
        print(display_top_songs.reset_index().to_string(index=False))
    else:
        print("  No songs found matching the criteria for top adopted songs.")

def analyze_adoption(export_results=True):
    """
    Main function to analyze adoption patterns and display results.
    
    Parameters:
    -----------
    export_results : bool
        Whether to export results to CSV files
    """
    # Load the data
    df = load_data()
    
    # Analyze adoption patterns
    results = analyze_adoption_patterns(df)
    
    # Display results
    display_adoption_results(results)
    
    # Export results if requested
    if export_results:
        export_adoption_results(results)

if __name__ == "__main__":
    analyze_adoption() 
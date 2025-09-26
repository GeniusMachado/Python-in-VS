"""
DR/IDR Case Study Indicator - Python Implementation
Converted from Pine Script v6

This indicator tracks Daily Range (DR) and Initial Daily Range (IDR) patterns,
providing statistical analysis and visualization of range holding patterns.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, time, timedelta
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

class DRIDRIndicator:
    def __init__(self, 
                 dr_session_start: str = "09:30",
                 dr_session_end: str = "10:30", 
                 extension_start: str = "10:30",
                 extension_end: str = "16:00",
                 break_logic: str = "wick",
                 track_rolling_n: int = 20,
                 risk_rr1: float = 1.0,
                 risk_rr2: float = 2.0):
        """
        Initialize the DR/IDR Indicator
        
        Parameters:
        -----------
        dr_session_start : str
            Start time for DR session (HH:MM format)
        dr_session_end : str  
            End time for DR session (HH:MM format)
        extension_start : str
            Start time for extension session (HH:MM format)
        extension_end : str
            End time for extension session (HH:MM format)
        break_logic : str
            Break detection logic: 'wick', 'close', or 'body'
        track_rolling_n : int
            Number of recent sessions to track for rolling statistics
        risk_rr1 : float
            First risk/reward target multiplier
        risk_rr2 : float
            Second risk/reward target multiplier
        """
        self.dr_session_start = dr_session_start
        self.dr_session_end = dr_session_end
        self.extension_start = extension_start
        self.extension_end = extension_end
        self.break_logic = break_logic.lower()
        self.track_rolling_n = track_rolling_n
        self.risk_rr1 = risk_rr1
        self.risk_rr2 = risk_rr2
        
        # Statistics tracking
        self.total_sessions = 0
        self.total_held = 0
        self.total_drh_success = 0
        self.total_drl_success = 0
        self.recent_results = []
        self.recent_labels = []
        self.recent_ranges = []
        
        # Current session state
        self.current_dr_high = None
        self.current_dr_low = None
        self.current_idr_high = None
        self.current_idr_low = None
        self.dr_active = False
        self.dr_broken = False
        self.bars_since_ext_end = 0
        
        # Results storage
        self.results = []
        
    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object"""
        return datetime.strptime(time_str, "%H:%M").time()
    
    def _is_in_session(self, timestamp: pd.Timestamp, start_time: str, end_time: str) -> bool:
        """Check if timestamp is within specified session"""
        start = self._parse_time(start_time)
        end = self._parse_time(end_time)
        current_time = timestamp.time()
        
        if start <= end:  # Same day session
            return start <= current_time <= end
        else:  # Overnight session
            return current_time >= start or current_time <= end
    
    def _is_dr_session(self, timestamp: pd.Timestamp) -> bool:
        """Check if timestamp is in DR session"""
        return self._is_in_session(timestamp, self.dr_session_start, self.dr_session_end)
    
    def _is_extension_session(self, timestamp: pd.Timestamp) -> bool:
        """Check if timestamp is in extension session"""
        return self._is_in_session(timestamp, self.extension_start, self.extension_end)
    
    def _detect_break(self, high: float, low: float, close: float, 
                     dr_high: float, dr_low: float) -> Tuple[bool, bool]:
        """Detect if DR has been broken"""
        break_high = False
        break_low = False
        
        if self.break_logic == "wick":
            if high > dr_high:
                break_high = True
            if low < dr_low:
                break_low = True
        elif self.break_logic == "close":
            if close > dr_high:
                break_high = True
            if close < dr_low:
                break_low = True
        elif self.break_logic == "body":
            # For body logic, we need open and close prices
            # This is simplified - in real implementation you'd need open prices
            if close > dr_high:
                break_high = True
            if close < dr_low:
                break_low = True
                
        return break_high, break_low
    
    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process OHLC data and calculate DR/IDR statistics
        
        Parameters:
        -----------
        df : pd.DataFrame
            DataFrame with columns: ['timestamp', 'open', 'high', 'low', 'close']
            
        Returns:
        --------
        pd.DataFrame
            Original dataframe with added DR/IDR columns
        """
        # Ensure timestamp column exists and is datetime
        if 'timestamp' not in df.columns:
            df = df.reset_index()
            if df.index.name == 'timestamp':
                df['timestamp'] = df.index
            else:
                raise ValueError("DataFrame must have a 'timestamp' column or datetime index")
        
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Initialize result columns
        df['dr_high'] = np.nan
        df['dr_low'] = np.nan
        df['idr_high'] = np.nan
        df['idr_low'] = np.nan
        df['dr_active'] = False
        df['dr_broken'] = False
        df['break_high'] = False
        df['break_low'] = False
        df['held'] = np.nan
        df['session_result'] = ""
        
        # Track session state
        current_session_start = None
        session_dr_high = None
        session_dr_low = None
        session_idr_high = None
        session_idr_low = None
        session_broken = False
        
        for i, row in df.iterrows():
            timestamp = row['timestamp']
            high = row['high']
            low = row['low']
            close = row['close']
            open_price = row.get('open', close)  # Use close as fallback if no open
            
            # Check if we're starting a new DR session
            is_dr_start = self._is_dr_session(timestamp)
            was_dr_session = i > 0 and self._is_dr_session(df.iloc[i-1]['timestamp'])
            
            if is_dr_start and not was_dr_session:
                # New DR session starting
                current_session_start = timestamp
                session_dr_high = high
                session_dr_low = low
                session_idr_high = max(open_price, close)
                session_idr_low = min(open_price, close)
                session_broken = False
                
                df.at[i, 'dr_active'] = True
                df.at[i, 'dr_high'] = session_dr_high
                df.at[i, 'dr_low'] = session_dr_low
                df.at[i, 'idr_high'] = session_idr_high
                df.at[i, 'idr_low'] = session_idr_low
                
            elif self._is_dr_session(timestamp) and current_session_start is not None:
                # Continue DR session
                session_dr_high = max(session_dr_high, high)
                session_dr_low = min(session_dr_low, low)
                session_idr_high = max(session_idr_high, max(open_price, close))
                session_idr_low = min(session_idr_low, min(open_price, close))
                
                df.at[i, 'dr_active'] = True
                df.at[i, 'dr_high'] = session_dr_high
                df.at[i, 'dr_low'] = session_dr_low
                df.at[i, 'idr_high'] = session_idr_high
                df.at[i, 'idr_low'] = session_idr_low
                
            elif self._is_extension_session(timestamp) and current_session_start is not None:
                # Extension session - check for breaks
                if not session_broken:
                    break_high, break_low = self._detect_break(
                        high, low, close, session_dr_high, session_dr_low
                    )
                    
                    if break_high or break_low:
                        session_broken = True
                        df.at[i, 'dr_broken'] = True
                        df.at[i, 'break_high'] = break_high
                        df.at[i, 'break_low'] = break_low
                
                # Update session values
                df.at[i, 'dr_high'] = session_dr_high
                df.at[i, 'dr_low'] = session_dr_low
                df.at[i, 'idr_high'] = session_idr_high
                df.at[i, 'idr_low'] = session_idr_low
                
            else:
                # Check if extension session just ended
                was_extension = i > 0 and self._is_extension_session(df.iloc[i-1]['timestamp'])
                if was_extension and current_session_start is not None:
                    # Session ended - evaluate results
                    held = not session_broken
                    self.total_sessions += 1
                    
                    if held:
                        self.total_held += 1
                    
                    # Track success rates
                    if session_broken:
                        if df.at[i-1, 'break_high']:
                            if close > session_dr_low:
                                self.total_drl_success += 1
                        if df.at[i-1, 'break_low']:
                            if close < session_dr_high:
                                self.total_drh_success += 1
                    
                    # Update rolling statistics
                    self.recent_results.append(1.0 if held else 0.0)
                    self.recent_labels.append("H" if held else "N")
                    self.recent_ranges.append(session_dr_high - session_dr_low)
                    
                    # Keep only last N results
                    if len(self.recent_results) > self.track_rolling_n:
                        self.recent_results.pop(0)
                        self.recent_labels.pop(0)
                        self.recent_ranges.pop(0)
                    
                    # Store result
                    result = {
                        'session_start': current_session_start,
                        'session_end': df.iloc[i-1]['timestamp'],
                        'dr_high': session_dr_high,
                        'dr_low': session_dr_low,
                        'idr_high': session_idr_high,
                        'idr_low': session_idr_low,
                        'held': held,
                        'broken': session_broken,
                        'range': session_dr_high - session_dr_low
                    }
                    self.results.append(result)
                    
                    # Mark the end of session
                    df.at[i-1, 'held'] = held
                    df.at[i-1, 'session_result'] = "HELD" if held else "NOT"
                    
                    # Reset session
                    current_session_start = None
                    session_dr_high = None
                    session_dr_low = None
                    session_idr_high = None
                    session_idr_low = None
                    session_broken = False
        
        return df
    
    def get_statistics(self) -> Dict:
        """Get current statistics"""
        rolling_count = len(self.recent_results)
        rolling_sum = sum(self.recent_results) if self.recent_results else 0
        rolling_pct = (rolling_sum / rolling_count * 100) if rolling_count > 0 else None
        
        overall_pct = (self.total_held / self.total_sessions * 100) if self.total_sessions > 0 else None
        drh_pct = (self.total_drh_success / self.total_sessions * 100) if self.total_sessions > 0 else None
        drl_pct = (self.total_drl_success / self.total_sessions * 100) if self.total_sessions > 0 else None
        
        avg_range = np.mean(self.recent_ranges) if self.recent_ranges else None
        
        return {
            'total_sessions': self.total_sessions,
            'overall_held_pct': overall_pct,
            'rolling_held_pct': rolling_pct,
            'drh_success_pct': drh_pct,
            'drl_success_pct': drl_pct,
            'avg_range': avg_range,
            'recent_labels': self.recent_labels[:10]  # Last 10 labels
        }
    
    def plot_results(self, df: pd.DataFrame, title: str = "DR/IDR Analysis", 
                    figsize: Tuple[int, int] = (15, 10)):
        """Plot the DR/IDR analysis results"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
        
        # Main price chart
        ax1.plot(df['timestamp'], df['close'], label='Close Price', alpha=0.7, linewidth=1)
        
        # Plot DR/IDR levels
        dr_high_data = df[df['dr_high'].notna()]
        dr_low_data = df[df['dr_low'].notna()]
        idr_high_data = df[df['idr_high'].notna()]
        idr_low_data = df[df['idr_low'].notna()]
        
        if not dr_high_data.empty:
            ax1.plot(dr_high_data['timestamp'], dr_high_data['dr_high'], 
                    'r-', linewidth=2, label='DR High', alpha=0.8)
        if not dr_low_data.empty:
            ax1.plot(dr_low_data['timestamp'], dr_low_data['dr_low'], 
                    'r-', linewidth=2, label='DR Low', alpha=0.8)
        if not idr_high_data.empty:
            ax1.plot(idr_high_data['timestamp'], idr_high_data['idr_high'], 
                    'g--', linewidth=1, label='IDR High', alpha=0.6)
        if not idr_low_data.empty:
            ax1.plot(idr_low_data['timestamp'], idr_low_data['idr_low'], 
                    'g--', linewidth=1, label='IDR Low', alpha=0.6)
        
        # Mark breaks and results
        break_high_data = df[df['break_high'] == True]
        break_low_data = df[df['break_low'] == True]
        held_data = df[df['session_result'] == 'HELD']
        not_held_data = df[df['session_result'] == 'NOT']
        
        if not break_high_data.empty:
            ax1.scatter(break_high_data['timestamp'], break_high_data['dr_high'], 
                       color='blue', marker='^', s=100, label='DRH Break', zorder=5)
        if not break_low_data.empty:
            ax1.scatter(break_low_data['timestamp'], break_low_data['dr_low'], 
                       color='blue', marker='v', s=100, label='DRL Break', zorder=5)
        if not held_data.empty:
            ax1.scatter(held_data['timestamp'], held_data['close'], 
                       color='green', marker='o', s=50, label='Held', zorder=5)
        if not not_held_data.empty:
            ax1.scatter(not_held_data['timestamp'], not_held_data['close'], 
                       color='red', marker='x', s=50, label='Not Held', zorder=5)
        
        ax1.set_title(title)
        ax1.set_ylabel('Price')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Statistics subplot
        stats = self.get_statistics()
        stats_text = f"""Statistics:
Total Sessions: {stats['total_sessions']}
Overall Held %: {stats['overall_held_pct']:.1f}% if stats['overall_held_pct'] else 'N/A'
Rolling Held %: {stats['rolling_held_pct']:.1f}% if stats['rolling_held_pct'] else 'N/A'
DRH Success %: {stats['drh_success_pct']:.1f}% if stats['drh_success_pct'] else 'N/A'
DRL Success %: {stats['drl_success_pct']:.1f}% if stats['drl_success_pct'] else 'N/A'
Avg Range: {stats['avg_range']:.2f} if stats['avg_range'] else 'N/A'
Recent: {''.join(stats['recent_labels'])}"""
        
        ax2.text(0.02, 0.5, stats_text, transform=ax2.transAxes, 
                fontsize=10, verticalalignment='center',
                bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.8))
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')
        
        plt.tight_layout()
        plt.show()
        
        return fig

def create_sample_data(start_date: str = "2024-01-01", 
                      end_date: str = "2024-01-31", 
                      freq: str = "5T") -> pd.DataFrame:
    """Create sample OHLC data for testing"""
    dates = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    # Generate realistic price data
    np.random.seed(42)
    n = len(dates)
    
    # Create trending price with some volatility
    base_price = 100
    trend = np.linspace(0, 20, n)  # 20 point trend over period
    noise = np.random.normal(0, 2, n)  # Random noise
    price = base_price + trend + noise
    
    # Generate OHLC data
    data = []
    for i, (timestamp, close) in enumerate(zip(dates, price)):
        # Add some intraday volatility
        volatility = np.random.uniform(0.5, 2.0)
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = close + np.random.uniform(-volatility/2, volatility/2)
        
        data.append({
            'timestamp': timestamp,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close
        })
    
    return pd.DataFrame(data)

# Example usage
if __name__ == "__main__":
    # Create sample data
    print("Creating sample data...")
    df = create_sample_data("2024-01-01", "2024-01-31", "5T")
    print(f"Created {len(df)} data points")
    
    # Initialize indicator
    indicator = DRIDRIndicator(
        dr_session_start="09:30",
        dr_session_end="10:30",
        extension_start="10:30", 
        extension_end="16:00",
        break_logic="wick",
        track_rolling_n=20
    )
    
    # Process data
    print("Processing data...")
    df_processed = indicator.process_data(df)
    
    # Get statistics
    stats = indicator.get_statistics()
    print("\nStatistics:")
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Plot results
    print("\nGenerating plot...")
    indicator.plot_results(df_processed, "DR/IDR Analysis - Sample Data")
    
    print("\nAnalysis complete!")

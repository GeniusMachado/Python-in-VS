import numpy as np
import multiprocessing as mp
from functools import partial
import time

# Use __slots__ for memory efficiency, reducing object overhead
class PointProcessor:
    __slots__ = ['points', 'threshold']
    def __init__(self, points, threshold):
        self.points = points
        self.threshold = threshold

# 1. Complexity: Vectorization (NumPy) - Avoids Python loops
def optimized_distance_calculation(points_subset, threshold):
    """Calculates pairwise distances for a subset using vectorized operations."""
    # NumPy operations are implemented in C, running at near C speed [3]
    diff = points_subset[:, np.newaxis, :] - points_subset[np.newaxis, :, :]
    dist = np.sqrt(np.sum(diff**2, axis=-1))
    return np.sum(dist < threshold)

def parallel_processing(data, threshold):
    # 2. Complexity: Multiprocessing - Bypasses GIL [2]
    num_cores = mp.cpu_count()
    # Split data among cores
    chunks = np.array_split(data, num_cores)
    
    # 3. Complexity: Functional Approach - partial for clean mapping
    pool = mp.Pool(processes=num_cores)
    func = partial(optimized_distance_calculation, threshold=threshold)
    results = pool.map(func, chunks)
    
    pool.close()
    pool.join()
    return sum(results)

if __name__ == '__main__':
    # Simulation: 10,000 points in 3D space
    print("Generating data...")
    data = np.random.rand(10000, 3)
    threshold = 0.05
    
    print(f"Processing {len(data)} points using {mp.cpu_count()} cores...")
    start_time = time.time()
    
    # Run the optimized function
    total_pairs = parallel_processing(data, threshold)
    
    end_time = time.time()
    print(f"Total pairs below threshold: {total_pairs}")
    print(f"Time taken: {end_time - start_time:.4f} seconds")
  
